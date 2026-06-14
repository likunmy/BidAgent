import asyncio
import json
import threading
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agent.graph.graph import bid_graph
from app.agent.graph.state import BidState
from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import file_service, project_service

router = APIRouter()

# Per-project event queues for SSE streaming
_project_queues: dict[int, asyncio.Queue] = {}
_queue_lock = threading.Lock()


def _get_or_create_queue(project_id: int) -> asyncio.Queue:
    """Get or create an event queue for a project (thread-safe)."""
    with _queue_lock:
        if project_id not in _project_queues:
            _project_queues[project_id] = asyncio.Queue()
        return _project_queues[project_id]


def _emit(project_id: int, event_type: str, **data):
    """Thread-safe: push an event to the project's async queue."""
    queue = _project_queues.get(project_id)
    if queue is None:
        return
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        return
    payload = {
        "type": event_type,
        **data,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    loop.call_soon_threadsafe(queue.put_nowait, payload)


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return project_service.list_projects(db)


@router.post("", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    return project_service.create_project(data, db)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return project_service.get_project(project_id, db)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    return project_service.update_project(project_id, data, db)


@router.get("/{project_id}/missing-infos")
def get_project_missing_infos(project_id: int, db: Session = Depends(get_db)):
    return file_service.get_project_missing_infos(project_id, db)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    success = project_service.delete_project(project_id, db)
    return {"success": success}


@router.get("/{project_id}/generate/stream")
async def stream_generation(project_id: int, db: Session = Depends(get_db)):
    """SSE endpoint: starts graph execution in background and streams progress."""
    queue = _get_or_create_queue(project_id)

    # Start graph in a background thread (only if not already running)
    thread = threading.Thread(
        target=_run_bid_graph,
        args=(project_id,),
        daemon=True,
    )
    thread.start()

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                event_type = event.pop("type", "step")

                if event_type == "complete":
                    yield f"event: complete\ndata: {json.dumps(event)}\n\n"
                    break
                if event_type == "error":
                    yield f"event: error\ndata: {json.dumps(event)}\n\n"
                    break

                yield f"event: step\ndata: {json.dumps(event)}\n\n"

                if event_type == "end":
                    break
        finally:
            with _queue_lock:
                _project_queues.pop(project_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _run_bid_graph(project_id: int):
    """Run the bid generation graph in a background thread."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        _emit(project_id, "step", step_id="init", name="初始化", status="in_progress")

        # Find tender document
        tender = file_service.get_tender_file(project_id, db)
        if not tender or not tender.md_path:
            _emit(project_id, "error", message="未找到招标文件，请先上传招标文件")
            return

        # Build initial state
        initial_state = BidState(
            project_id=project_id,
            tender_md_path=tender.md_path,
            tender_content="",
            requirements=[],
            outline=[],
            chapters=[],
            current_chapter_index=0,
            completed_chapter_ids=[],
            docx_path=None,
            final_review_result=None,
            final_review_round=0,
            max_parallel=6,
            max_revisions=3,
            max_final_rounds=2,
        )

        config = {
            "configurable": {
                "event_callback": lambda type, **data: _emit(project_id, type, **data),
            }
        }

        _emit(project_id, "step", step_id="init", name="初始化完成", status="completed")

        # Run the graph
        result = bid_graph.invoke(initial_state, config)

        if result.get("final_review_result") == "PASS":
            _emit(project_id, "complete",
                  step_id="done",
                  name="标书生成完成",
                  status="completed",
                  file_path=result.get("docx_path", ""))
        else:
            _emit(project_id, "complete",
                  step_id="done",
                  name="标书生成结束",
                  status="completed",
                  note="终审存在问题，请检查后手动调整",
                  file_path=result.get("docx_path", ""))

    except Exception as e:
        _emit(project_id, "error", message=f"生成失败: {str(e)}")
    finally:
        db.close()
