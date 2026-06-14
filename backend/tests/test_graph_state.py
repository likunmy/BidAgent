"""Tests for graph state and chapter lifecycle."""

from app.agent.graph.state import ChapterTask


def test_chapter_task_defaults():
    """ChapterTask should have sensible defaults."""
    task = ChapterTask(id="ch_01", title="技术方案")
    assert task.status == "pending"
    assert task.content is None
    assert task.review_feedback is None
    assert task.revision_count == 0
    assert task.missing_items == []


def test_chapter_task_with_constraints():
    """ChapterTask should accept constraints list."""
    task = ChapterTask(
        id="ch_01",
        title="技术方案",
        constraints=["要求1: 需包含系统架构图", "要求2: 需说明安全措施"],
    )
    assert len(task.constraints) == 2


def test_chapter_task_status_transitions():
    """ChapterTask status should be settable."""
    task = ChapterTask(id="ch_01", title="技术方案")
    task.status = "in_progress"
    assert task.status == "in_progress"
    task.status = "completed"
    assert task.status == "completed"


def test_chapter_task_revision_tracking():
    """ChapterTask should track revision count and feedback."""
    task = ChapterTask(id="ch_01", title="技术方案")
    task.revision_count = 1
    task.review_feedback = "缺少系统架构图"
    assert task.revision_count == 1
    assert task.review_feedback == "缺少系统架构图"
