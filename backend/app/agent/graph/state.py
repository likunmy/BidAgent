from typing import Annotated, TypedDict

from pydantic import BaseModel


class ChapterTask(BaseModel):
    id: str
    title: str
    constraints: list[str] = []
    status: str = "pending"  # pending | in_progress | completed | failed
    content: str | None = None
    review_feedback: str | None = None
    revision_count: int = 0
    missing_items: list[dict] = []


def _reduce_chapters(current: list[ChapterTask], update: list[ChapterTask]) -> list[ChapterTask]:
    """Merge chapter updates by id so parallel writes don't conflict."""
    if not update:
        return current or []
    if not current:
        return update
    merged = {c.id: c for c in current}
    for c in update:
        merged[c.id] = c
    return list(merged.values())


class BidState(TypedDict):
    # Read-only context
    project_id: int
    tender_md_path: str

    # Phase 1: parse result
    tender_content: str
    requirements: list[str]
    outline: list[dict]

    # Phase 2: chapter execution
    chapters: Annotated[list[ChapterTask], _reduce_chapters]
    current_chapter_index: int
    completed_chapter_ids: list[str]

    # Phase 3: docx
    docx_path: str | None

    # Phase 4: final review
    final_review_result: str | None
    final_review_round: int

    # Controls
    max_parallel: int
    max_revisions: int
    max_final_rounds: int
