"""Tests for agent tools — verifying input/output schemas."""

from app.agent.tools.docx_output import OutputDocxInput, ParagraphBlock, Section
from app.agent.tools.file_loader import LoadFileInput
from app.agent.tools.file_search import FileSearchInput, FileSearchOutput
from app.agent.tools.missing_info import MissingItem, StoreMissingInfoInput, StoreMissingInfoOutput


def test_file_search_schema():
    """FileSearchInput should require project_id and query."""
    data = FileSearchInput(project_id=1, query="test")
    assert data.project_id == 1
    assert data.query == "test"


def test_file_search_optional_filter():
    """filename_filter should be optional."""
    data = FileSearchInput(project_id=1, query="test", filename_filter="技术")
    assert data.filename_filter == "技术"


def test_file_loader_schema():
    """LoadFileInput should require file_path."""
    data = LoadFileInput(file_path="/path/to/file.md")
    assert data.file_path == "/path/to/file.md"


def test_file_loader_with_section():
    """section_heading should be optional."""
    data = LoadFileInput(file_path="/path/to/file.md", section_heading="技术方案")
    assert data.section_heading == "技术方案"


def test_store_missing_info_schema():
    """StoreMissingInfoInput should accept items list."""
    items = [
        MissingItem(name="营业执照", description="需要企业营业执照"),
        MissingItem(name="资质证书", description="需要相关资质"),
    ]
    data = StoreMissingInfoInput(project_id=1, items=items)
    assert data.project_id == 1
    assert len(data.items) == 2
    assert data.items[0].name == "营业执照"


def test_missing_item_optional_description():
    """MissingItem description should be optional."""
    item = MissingItem(name="测试项")
    assert item.description is None


def test_docx_output_schema():
    """OutputDocxInput should accept sections with various block types."""
    section = Section(
        heading="第一章",
        level=1,
        children=[
            ParagraphBlock(type="paragraph", text="内容测试"),
        ],
    )
    data = OutputDocxInput(
        project_id=1,
        output_filename="test.docx",
        sections=[section],
    )
    assert len(data.sections) == 1
    assert data.sections[0].children[0].text == "内容测试"


def test_docx_output_append_mode():
    """append_to_existing should default to False."""
    data = OutputDocxInput(project_id=1, output_filename="test.docx", sections=[])
    assert data.append_to_existing is False


def test_output_schema():
    """Ensure all tool outputs have expected fields."""
    fs_out = FileSearchOutput(total=0, results=[])
    assert fs_out.total == 0

    sm_out = StoreMissingInfoOutput(stored=2, items=[])
    assert sm_out.stored == 2
