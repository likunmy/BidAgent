# Agent 图编排设计

## 概述

在现有 4 个 agent 工具的基础上，使用 LangGraph StateGraph 编排完整的标书生成流程：

1. 主 agent 解析招标文件 → 生成大纲 → 创建章节任务
2. 最多 6 个子 agent 并行执行章节任务
3. 审核 agent 逐章审核，不通过则打回修改（最多 3 轮）
4. 终审 agent 加载原始招标 + 最终 docx 做全篇审核（最多 2 轮）

## 架构总览

```
                    ┌──────────────────────────────────────┐
                    │         LangGraph StateGraph          │
                    │                                       │
  【主agent】       【章节agent×N(≤6)】   【审核agent】   【终审agent】
  parse_tender ──→ create_tasks ──→ execute_chapter ──→ review_chapter
       │                              ↻ if fail          │
       │                              3轮上限          pass
       │                                                ▼
       │                                         compile_chapter
       │                                                │
       │                                          全部完成?
       │                                          ↙      ↘
       │                                    还有任务    全部完成
       │                                      │          │
       └──────────────────────────────────────┘    final_review
                                                      │
                                                   pass/fail
                                                      │
                                                  END / 打回
```

## 状态设计

```python
class ChapterTask(BaseModel):
    id: str
    title: str
    constraints: list[str]
    status: Literal["pending", "in_progress", "completed", "failed"]
    content: str | None = None          # Markdown 格式章节内容
    review_feedback: str | None = None  # 审核意见
    revision_count: int = 0
    missing_items: list[MissingItem] = []

class BidState(TypedDict):
    # 只读上下文
    project_id: int
    tender_md_path: str

    # 阶段 1: 解析结果
    tender_content: str
    requirements: list[str]             # 所有招标要求
    outline: list[dict]                 # 标书大纲

    # 阶段 2: 章节任务
    chapters: list[ChapterTask]
    current_chapter_index: int          # 已分配到的章节索引
    active_chapters: list[str]          # 正在执行中的章节 ID
    completed_chapter_ids: list[str]

    # 阶段 3: docx 编译
    docx_path: str | None

    # 阶段 4: 终审
    final_review_result: str | None
    final_missing_items: list[MissingItem]

    # 运行控制
    max_parallel: int = 6
    max_revisions: int = 3
    max_final_rounds: int = 2
    final_review_round: int = 0
```

## 图节点

| 节点 | 角色 | 功能 |
|------|------|------|
| `parse_tender` | 主 agent | 加载招标文件 MD，提取全部招标要求，生成标书大纲 |
| `create_tasks` | 主 agent | 将大纲拆分为章节任务，每章附带约束条件 |
| `execute_chapter` | 章节 agent | 接收一个章节任务，生成 Markdown 内容，可调用工具查询文件 |
| `review_chapter` | 审核 agent | 审核章节内容是否满足约束条件，输出 PASS/FAIL + 意见 |
| `route_review` | 路由 | 代码逻辑判断：pass → 编译，fail & 未超限 → 修改，超限 → failed |
| `compile_chapter` | 主 agent | 将通过的章节内容追加到 docx |
| `check_completion` | 路由 | 判断所有章节完成 → 终审，否则派发下一批 |
| `final_review` | 终审 agent | 加载招标 MD + 最终 docx 全篇审核 |
| `route_final` | 路由 | pass → END，fail → 创建修改任务重新执行 |

### 路由逻辑

```python
def route_review(state, chapter_id):
    """审核结果路由：pass / revise / abort"""
    chapter = next(c for c in state["chapters"] if c.id == chapter_id)
    if chapter.review_feedback is None:
        return "pass"
    if chapter.revision_count >= state["max_revisions"]:
        return "abort"   # 超限，标记 failed 继续
    return "revise"

def check_completion(state):
    """检查所有章节是否完成"""
    if all(c.status in ("completed", "failed") for c in state["chapters"]):
        return "final_review"
    return "dispatch_more"

def route_final(state):
    """终审结果路由"""
    if state["final_review_result"] == "PASS":
        return "end"
    return "revision"
```

### 并行控制

`dispatch_chapters` 节点每次计算可派发的任务数：
- 上限 6，减去当前 `active_chapters` 中的数量
- 从 `chapters[current_chapter_index:]` 中取 pending 状态的发送
- 使用 `Send()` 为每个任务创建独立分支

```
每个分支独立执行: execute_chapter → review_chapter → route_review → (compile_chapter / revise)
所有分支在 check_completion 处收敛
```

## Agent 详细定义

### 主 agent

**系统提示要点：**
- 标书编制专家，负责解析招标文件和规划标书结构
- 必须完整读取招标文件全文，不得遗漏任何要求
- 提取的招标要求包括：投标人资格、评分标准、技术规范、商务条款、交付要求、格式要求等

**工具：** file_loader（加载招标 MD），file_search（查询参考文件），output_docx（编译 docx）

**在 parse_tender 节点中：**
1. 调用 file_loader 加载招标文件全文
2. 将所有招标要求以列表形式提取
3. 生成标书大纲，每章标注须遵循的招标要求 ID

**在 create_tasks 节点中：**
1. 将大纲转为 ChapterTask 列表
2. 每个 task 的 constraints 包含对应的招标要求原文

**在 compile_chapter 节点中：**
1. 将通过的章节内容（Markdown）转为 Section 结构
2. 调用 output_docx(append_to_existing=True) 追加到 docx

### 章节生成 agent

**系统提示要点：**
- 标书章节撰写专家，只负责撰写指定的一个章节
- 必须严格遵守约束条件中的招标要求
- 可以查询项目文件中的资料来支撑内容
- 如果发现需要的资料缺失，调用 store_missing_info 记录
- 输出格式为 Markdown，图片引用使用 `[图: md5=xxx, 尺寸=WxH]`

**工具：** file_search, file_loader, store_missing_info

**输入（来自 Send 的 task 参数）：**
```json
{
  "chapter_id": "ch_03",
  "title": "技术方案",
  "constraints": ["要求2: 须提供详细的系统架构图", "要求4: 须说明安全防护措施"]
}
```

### 审核 agent

**系统提示要点：**
- 标书质量审核专家
- 专注于判断章节内容是否满足所有约束条件对应的招标要求
- 不修改任何内容，只输出审核意见

**规则：**
- 不调用任何工具，纯 LLM 判断
- 输出格式：`PASS` 或 `FAIL:\n- 问题1\n- 问题2\n...`

### 终审 agent

**系统提示要点：**
- 标书终审专家，对标书整体质量负最终责任
- 加载招标文件 MD（file_loader）和最终 docx（file_loader 加载后阅读）
- 逐项核对招标要求是否被充分响应
- 检查整体逻辑连贯性、格式规范

**工具：** file_loader（加载招标和 docx），file_search（查漏补缺）

**输出：** `PASS` 或 `FAIL:\n- [章节ID] 具体问题\n...`

## 工具修改

### output_docx 追加模式

当前 `output_docx` 从零生成完整 docx。修改为支持追加到已有文件：

```python
class OutputDocxInput(BaseModel):
    project_id: int
    output_filename: str
    sections: list[Section]
    append_to_existing: bool = False   # 新增字段
```

`append_to_existing=True` 时：
1. 检查输出文件是否已存在
2. 如果存在则加载（python-docx 的 `Document()` 打开已有文件）
3. 在其末尾追加新 sections
4. 保存回原路径
5. 如果文件不存在则走新建逻辑

## 文件结构

```
backend/app/agent/
  __init__.py
  tool_registry.py
  graph/
    __init__.py
    state.py              # BidState, ChapterTask 定义
    prompts.py            # 各 agent 的系统提示词
    nodes.py              # 所有 agent 节点函数
    router.py             # 条件边路由函数
    graph.py              # 构建 LangGraph StateGraph
    agent_factory.py      # 创建 LLM agent 执行器 (OpenAI-compatible)
  tools/
    ... (现有不变)
```

## 新增依赖

```bash
pip install langgraph langchain-openai
```

环境变量：
- `DEEPSEEK_API_KEY` — DeepSeek API Key
- `DEEPSEEK_BASE_URL` — DeepSeek API Base URL（默认 `https://api.deepseek.com/v1`）

## 错误处理

- **单章节超限失败**：不影响其他章节，该章节标记 failed，流程继续
- **终审超限**：以最后一次评审结果为准，输出含备注说明
- **LLM 调用失败**：单个 agent 调用失败时重试 2 次，仍失败则标记对应章节 failed
- **docx 写入失败**：compile_chapter 节点捕获异常，输出错误信息到 state

## 后续优化空间

- 支持中断恢复（保存 graph 状态快照）
- 引入人工审核节点（在审核/终审环节插入人工决策点）
- 按章节类型分配不同的子 agent 提示词（技术方案 vs 商务条款 vs 公司介绍）
