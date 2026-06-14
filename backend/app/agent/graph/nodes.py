"""Graph node functions — each is a LangGraph node that receives state
and returns a partial state update.

NOTE: Chapter parallelism is handled within execute_batch via
ThreadPoolExecutor (up to 6 workers), not via LangGraph Send().
This keeps the graph structure simple and avoids reducer complexity.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

from docx import Document as DocxDocument
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from app.agent.graph.agent_factory import (
    build_chapter_agent,
    build_final_review_agent,
    build_main_agent,
    build_review_agent,
)
from app.agent.graph.prompts import (
    CHAPTER_WRITER_SYSTEM,
    FINAL_REVIEWER_SYSTEM,
    MAIN_AGENT_SYSTEM,
    REVIEWER_SYSTEM,
)
from app.agent.graph.state import BidState, ChapterTask
from app.agent.tools.docx_output import (
    ImageBlock,
    OutputDocxInput,
    ParagraphBlock,
    Section,
    TableBlock,
    output_docx,
)
from app.agent.tools.file_loader import LoadFileInput, load_file
from app.agent.tools.file_search import FileSearchInput, file_search
from app.agent.tools.missing_info import (
    StoreMissingInfoInput,
    store_missing_info,
)
from app.core.database import SessionLocal

# ---------------------------------------------------------------------------
# Tool calling helpers
# ---------------------------------------------------------------------------


def _call_agent(llm, messages: list, max_rounds: int = 5) -> str:
    """Invoke LLM with tool-calling loop. Returns final content string."""
    response = llm.invoke(messages)
    for _ in range(max_rounds):
        if not response.tool_calls:
            break
        messages.append(response)
        for tc in response.tool_calls:
            result = _exec_tool(tc["name"], tc["args"])
            content = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else str(result)
            messages.append(ToolMessage(content=content, tool_call_id=tc["id"]))
        response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def _exec_tool(name: str, args: dict) -> Any:
    """Execute a tool by name, creating a fresh DB session if needed."""
    db = None
    try:
        if name == "load_file":
            return load_file(LoadFileInput(**args))
        if name == "file_search":
            db = SessionLocal()
            return _serial(file_search(FileSearchInput(**args), db=db))
        if name == "store_missing_info":
            db = SessionLocal()
            return _serial(store_missing_info(StoreMissingInfoInput(**args), db=db))
        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error: {e}"
    finally:
        if db:
            db.close()


def _serial(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def parse_tender(state: BidState, config: RunnableConfig) -> dict:
    """Phase 1: load tender MD → LLM extracts requirements + outline."""
    cb = config.get("configurable", {}).get("event_callback")
    if cb:
        cb("step", step_id="parse", name="解析招标文件", status="in_progress")

    llm = build_main_agent()

    tender_content = load_file(LoadFileInput(file_path=state["tender_md_path"])).content

    prompt = f"""请解析以下招标文件，提取所有招标要求，并生成标书大纲。

招标文件内容：
{tender_content}

请按以下 JSON 格式输出（不要包含其他文字）：

```json
{{
  "requirements": ["要求1原文", "要求2原文", ...],
  "outline": [
    {{"id": "ch_01", "title": "章节标题", "constraint_indices": [0, 2]}},
    ...
  ]
}}
```

其中 constraint_indices 是该章节必须遵守的招标要求在 requirements 数组中的索引。
大纲应覆盖标书的所有必要章节，通常包括但不限于：公司简介、资质证明、技术方案、项目管理、商务报价、售后服务等。"""

    messages = [SystemMessage(content=MAIN_AGENT_SYSTEM), HumanMessage(content=prompt)]
    result = _call_agent(llm, messages)
    parsed = _parse_json(result)
    requirements = parsed.get("requirements", [])
    outline = parsed.get("outline", [])

    if cb:
        cb("step", step_id="parse", name="解析招标文件", status="completed",
           detail=f"提取 {len(requirements)} 条要求，生成 {len(outline)} 个章节")

    return {
        "tender_content": tender_content,
        "requirements": requirements,
        "outline": outline,
    }


def create_tasks(state: BidState, config: RunnableConfig) -> dict:
    """Convert outline to ChapterTask list."""
    chapters: list[ChapterTask] = []
    for item in state["outline"]:
        indices = item.get("constraint_indices", [])
        constraints = [state["requirements"][i] for i in indices if i < len(state["requirements"])]
        chapters.append(ChapterTask(
            id=item["id"],
            title=item.get("title", ""),
            constraints=constraints,
        ))
    return {
        "chapters": chapters,
        "current_chapter_index": len(chapters),
        "completed_chapter_ids": [],
        "docx_path": None,
    }


def execute_batch(state: BidState, config: RunnableConfig) -> dict:
    """Run pending chapters in parallel (up to max_parallel).
    Each chapter gets its own execute-review-revise loop.
    """
    cb = config.get("configurable", {}).get("event_callback")
    pending = [c for c in state["chapters"] if c.status == "pending"]
    active_count = len([c for c in state["chapters"] if c.status == "in_progress"])
    max_workers = min(state.get("max_parallel", 6) - active_count, len(pending))
    if max_workers == 0:
        return {}

    if cb:
        cb("step", step_id="chapters", name=f"生成章节 (×{max_workers})", status="in_progress")

    updated = {c.id: c for c in state["chapters"]}
    docx_path = state.get("docx_path")

    def process_one(chapter: ChapterTask) -> list[ChapterTask]:
        """Full execute-review-revise loop for a single chapter."""
        local_updated = {chapter.id: chapter}

        # Mark in_progress
        chapter = chapter.model_copy(update={"status": "in_progress"})
        local_updated[chapter.id] = chapter

        while chapter.revision_count <= state.get("max_revisions", 3):
            # === EXECUTE ===
            writer_llm = build_chapter_agent()
            constraints_text = "\n".join(f"- {c}" for c in chapter.constraints) if chapter.constraints else "无特殊约束"
            feedback = f"\n\n上次审核意见（请据此修改）：\n{chapter.review_feedback}" if chapter.review_feedback else ""
            prompt = f"""请撰写标书章节: 【{chapter.title}】

该章节必须遵守的招标要求：
{constraints_text}{feedback}

请用 Markdown 格式输出章节内容。
如果需要引用项目文件中的资料，请使用 file_search 和 file_loader 工具查询。
如果发现需要的资料缺失，请使用 store_missing_info 工具记录。
图片引用请使用 [图: md5=xxx, 尺寸=WxH] 格式。"""

            msgs = [SystemMessage(content=CHAPTER_WRITER_SYSTEM), HumanMessage(content=prompt)]
            content = _call_agent(writer_llm, msgs)
            chapter = chapter.model_copy(update={"content": content})

            # === REVIEW ===
            review_llm = build_review_agent()
            review_prompt = f"""请审核以下章节内容是否满足所有招标要求。

章节标题：{chapter.title}

必须遵守的招标要求：
{constraints_text}

章节内容：
{chapter.content}

请仔细审核，输出 PASS 或 FAIL（包含具体问题）。"""

            review_msgs = [SystemMessage(content=REVIEWER_SYSTEM), HumanMessage(content=review_prompt)]
            review_result = _call_agent(review_llm, review_msgs)

            if review_result.strip().startswith("PASS"):
                chapter = chapter.model_copy(update={
                    "status": "completed",
                    "review_feedback": None,
                })
                local_updated[chapter.id] = chapter
                return list(local_updated.values())
            else:
                new_rev = chapter.revision_count + 1
                if new_rev >= state.get("max_revisions", 3):
                    chapter = chapter.model_copy(update={
                        "status": "failed",
                        "review_feedback": review_result,
                        "revision_count": new_rev,
                    })
                    local_updated[chapter.id] = chapter
                    return list(local_updated.values())

                chapter = chapter.model_copy(update={
                    "review_feedback": review_result,
                    "revision_count": new_rev,
                })
                local_updated[chapter.id] = chapter

        return list(local_updated.values())

    # Run chapters in parallel
    chapters_to_run = pending[:max_workers]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, c): c for c in chapters_to_run}
        for future in as_completed(futures):
            try:
                result_list = future.result()
                for c in result_list:
                    updated[c.id] = c
            except Exception as e:
                c = futures[future]
                updated[c.id] = updated[c.id].model_copy(update={
                    "status": "failed",
                    "review_feedback": f"执行异常: {e}",
                })

    # Compile completed chapters to docx
    for c in updated.values():
        if c.status == "completed" and c.id not in state.get("completed_chapter_ids", []):
            db = SessionLocal()
            try:
                sections = _md_to_sections(c.title, c.content or "")
                output = output_docx(OutputDocxInput(
                    project_id=state["project_id"],
                    output_filename="投标文件.docx",
                    sections=sections,
                    append_to_existing=True,
                ), db=db)
                docx_path = output.file_path
            except Exception:
                pass
            finally:
                db.close()

    completed_ids = list(set(state.get("completed_chapter_ids", [])) | {c.id for c in updated.values() if c.status == "completed"})

    if cb:
        cb("step", step_id="chapters", name="章节生成完成", status="completed",
           detail=f"已完成 {len(completed_ids)}/{len(state['chapters'])} 章")

    return {
        "chapters": list(updated.values()),
        "completed_chapter_ids": completed_ids,
        "docx_path": docx_path,
    }


def final_review(state: BidState, config: RunnableConfig) -> dict:
    """Final review: compare original tender with final docx."""
    cb = config.get("configurable", {}).get("event_callback")
    if cb:
        cb("step", step_id="final_review", name="终审", status="in_progress")

    llm = build_final_review_agent()
    docx_text = _extract_docx_text(state.get("docx_path"))

    prompt = f"""请对完整标书进行终审。

原始招标文件：
{state["tender_content"]}

最终标书内容：
{docx_text}

请逐项核对招标要求是否在标书中得到充分响应。
检查整体逻辑连贯性、格式规范。

输出 PASS 或 FAIL（包含具体问题及对应章节）。"""

    messages = [SystemMessage(content=FINAL_REVIEWER_SYSTEM), HumanMessage(content=prompt)]
    result = _call_agent(llm, messages)
    is_pass = result.strip().startswith("PASS")

    if cb:
        cb("step", step_id="final_review", name="终审", status="completed" if is_pass else "failed",
           detail="PASS" if is_pass else "存在问题，需修改")

    return {
        "final_review_result": "PASS" if is_pass else result,
        "final_review_round": state.get("final_review_round", 0) + 1,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM output (handles markdown code fences)."""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def _md_to_sections(heading: str, md_content: str) -> list[Section]:
    """Convert Markdown chapter content to docx Section blocks."""
    children: list = []
    lines = md_content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        img_match = re.match(r"\[图:\s*md5=(\w+),\s*尺寸=(\d+)x(\d+)\]", line.strip())
        if img_match:
            children.append(ImageBlock(
                type="image",
                source_md_path="",
                md5=img_match.group(1),
                width=int(img_match.group(2)),
                height=int(img_match.group(3)),
            ))
            i += 1
            continue

        if line.strip().startswith("|") and line.strip().endswith("|"):
            rows_data = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows_data.append(cells)
                i += 1
            if len(rows_data) >= 2:
                if len(rows_data) > 1 and re.match(r"^[\s\|:\-]+$", rows_data[1][0] if rows_data[1] else ""):
                    header_row = rows_data[0]
                    data_rows = rows_data[2:]
                else:
                    header_row = rows_data[0]
                    data_rows = rows_data[1:]
                children.append(TableBlock(type="table", headers=header_row, rows=[r[:len(header_row)] for r in data_rows]))
            continue

        if line.strip():
            children.append(ParagraphBlock(type="paragraph", text=line.strip()))
        i += 1

    return [Section(heading=heading, level=1, children=children)]


def _extract_docx_text(path: str | None) -> str:
    if not path:
        return ""
    try:
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        return "(无法读取 docx 文件)"
