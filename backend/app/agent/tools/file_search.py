from pathlib import Path

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.file import File


class FileSearchInput(BaseModel):
    project_id: int
    query: str
    filename_filter: str | None = None


class SearchResult(BaseModel):
    file_path: str
    display_name: str
    snippets: list[str]
    match_count: int


class FileSearchOutput(BaseModel):
    total: int
    results: list[SearchResult]


def file_search(input_data: FileSearchInput, db: Session) -> FileSearchOutput:
    """Search MD file contents within a project and public directories.

    Excludes the tender document's MD file. Supports optional filename filter.
    """
    query_lower = input_data.query.lower()

    # Collect candidate md_paths
    md_paths: list[tuple[str, str]] = []  # (file_path, display_name)

    # 1. Project files (exclude tender)
    project_files = (
        db.query(File)
        .filter(File.project_id == input_data.project_id)
        .all()
    )
    for f in project_files:
        if f.file_type == "tender":
            continue
        if f.md_path:
            fp = Path(f.md_path)
            if fp.exists() and fp.suffix == ".md":
                md_paths.append((str(fp), f.display_name or ""))

    # 2. Public files
    public_files = (
        db.query(File)
        .filter(File.file_type == "public")
        .all()
    )
    for f in public_files:
        if f.md_path:
            fp = Path(f.md_path)
            if fp.exists() and fp.suffix == ".md":
                md_paths.append((str(fp), f.display_name or ""))

    # Optional filename filter
    if input_data.filename_filter:
        filt = input_data.filename_filter.lower()
        md_paths = [(p, n) for p, n in md_paths if filt in p.lower() or filt in n.lower()]

    # Search content
    results: list[SearchResult] = []
    for file_path, display_name in md_paths:
        try:
            content = Path(file_path).read_text(encoding="utf-8")
        except Exception:
            continue

        if query_lower not in content.lower():
            continue

        lines = content.splitlines()
        match_count = 0
        snippets: list[str] = []

        for i, line in enumerate(lines):
            if query_lower in line.lower():
                match_count += 1
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                snippet = "\n".join(lines[start:end])
                if snippet not in snippets:
                    snippets.append(snippet)

        if match_count > 0:
            results.append(SearchResult(
                file_path=file_path,
                display_name=display_name,
                snippets=snippets,
                match_count=match_count,
            ))

    return FileSearchOutput(total=len(results), results=results)
