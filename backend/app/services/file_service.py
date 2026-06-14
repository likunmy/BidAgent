import re
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from markitdown import MarkItDown
from sqlalchemy.orm import Session

from app.agent.tools.image_extractor import extract_images_from_source
from app.core.config import settings
from app.models.file import File
from app.models.missing_info import MissingInfo

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Magic bytes for file type validation
_FILE_SIGNATURES = {
    ".pdf": [b"%PDF"],
    ".docx": [b"PK\x03\x04"],
}


def _validate_file_signature(content: bytes, ext: str, filename: str):
    sigs = _FILE_SIGNATURES.get(ext, [])
    if not sigs:
        return  # txt: no signature check
    for sig in sigs:
        if content[:len(sig)] == sig:
            return
    hints = {
        ".pdf": "文件头不是 %PDF，请确认文件是否是真实的 PDF 文件",
        ".docx": "文件头不是 ZIP 格式（PK），请确认文件是否是真实的 .docx 文件（而非 .doc 改名）",
    }
    raise HTTPException(
        status_code=400,
        detail=f"文件格式校验失败: {hints.get(ext, '文件可能已损坏')}",
    )


def _sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", name).strip() or "unnamed"


def _unique_path(directory: Path, stem: str, ext: str) -> Path:
    path = directory / f"{stem}{ext}"
    counter = 1
    while path.exists():
        path = directory / f"{stem}_{counter}{ext}"
        counter += 1
    return path


def upload_public_file(file: UploadFile, display_name: str, description: str | None, db: Session) -> File:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}, 仅支持 PDF/DOCX/TXT")

    format_name = ext.lstrip(".")
    content = file.file.read()
    _validate_file_signature(content, ext, file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Save original to data/{format}/
    src_stem = Path(file.filename).stem
    src_filename = f"{src_stem}_{timestamp}{ext}"
    data_dir = Path(settings.data_dir) / format_name
    data_dir.mkdir(parents=True, exist_ok=True)
    src_path = data_dir / src_filename
    src_path.write_bytes(content)

    try:
        # 2. Convert to MD
        md = MarkItDown()
        result = md.convert(str(src_path))

        # 3. Save MD to uploads/public/{display_name}.md
        safe_name = _sanitize_filename(display_name) or src_stem
        uploads_public = Path(settings.upload_dir) / "public"
        uploads_public.mkdir(parents=True, exist_ok=True)

        md_path = _unique_path(uploads_public, safe_name, ".md")
        md_path.write_text(result.text_content, encoding="utf-8")

        # 3.5 Extract embedded images from source
        extract_images_from_source(src_path, md_path)

        # 4. DB record
        db_file = File(
            display_name=display_name,
            description=description,
            original_name=file.filename,
            source_format=format_name,
            source_path=str(src_path),
            md_path=str(md_path),
            file_type="public",
            size=len(content),
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

    except Exception as e:
        if src_path.exists():
            src_path.unlink()
        raise HTTPException(status_code=500, detail=f"文件转换失败: {str(e)}")


def upload_project_file(file: UploadFile, display_name: str, description: str | None, project_id: int, db: Session) -> File:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}, 仅支持 PDF/DOCX/TXT")

    format_name = ext.lstrip(".")
    content = file.file.read()
    _validate_file_signature(content, ext, file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Save original to data/{format}/
    src_stem = Path(file.filename).stem
    src_filename = f"{src_stem}_{timestamp}{ext}"
    data_dir = Path(settings.data_dir) / format_name
    data_dir.mkdir(parents=True, exist_ok=True)
    src_path = data_dir / src_filename
    src_path.write_bytes(content)

    try:
        # 2. Convert to MD
        md = MarkItDown()
        result = md.convert(str(src_path))

        # 3. Save MD to uploads/projects/{project_id}/{display_name}.md
        safe_name = _sanitize_filename(display_name) or src_stem
        uploads_project = Path(settings.upload_dir) / "projects" / str(project_id)
        uploads_project.mkdir(parents=True, exist_ok=True)

        md_path = _unique_path(uploads_project, safe_name, ".md")
        md_path.write_text(result.text_content, encoding="utf-8")

        # 3.5 Extract embedded images from source
        extract_images_from_source(src_path, md_path)

        # 4. DB record
        db_file = File(
            display_name=display_name,
            description=description,
            original_name=file.filename,
            source_format=format_name,
            source_path=str(src_path),
            md_path=str(md_path),
            file_type="project",
            size=len(content),
            project_id=project_id,
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

    except Exception as e:
        if src_path.exists():
            src_path.unlink()
        raise HTTPException(status_code=500, detail=f"文件转换失败: {str(e)}")


def upload_tender_file(file: UploadFile, project_id: int, db: Session) -> File:
    """Upload a file as the tender document (saved as 招标文件.md).
    If a tender file already exists, its files and DB record are fully replaced.
    """
    existing = db.query(File).filter(
        File.project_id == project_id,
        File.file_type == "tender"
    ).first()
    if existing:
        # Delete old files from disk
        old_src = Path(existing.source_path)
        old_md = Path(existing.md_path)
        if old_src.exists():
            old_src.unlink()
        if old_md.exists():
            old_md.unlink()
        # Remove old DB record
        db.delete(existing)
        db.flush()

    # Upload fresh — _unique_path won't conflict since old files are gone
    db_file = upload_project_file(file, "招标文件", None, project_id, db)
    db_file.file_type = "tender"
    db.commit()
    db.refresh(db_file)
    return db_file


def get_tender_file(project_id: int, db: Session) -> File | None:
    return (
        db.query(File)
        .filter(File.project_id == project_id, File.file_type == "tender")
        .order_by(File.created_at.desc())
        .first()
    )


def get_project_missing_infos(project_id: int, db: Session) -> list[MissingInfo]:
    return (
        db.query(MissingInfo)
        .filter(MissingInfo.project_id == project_id)
        .order_by(MissingInfo.created_at.desc())
        .all()
    )


def list_project_files(project_id: int, db: Session) -> list[File]:
    return (
        db.query(File)
        .filter(File.file_type == "project", File.project_id == project_id)
        .order_by(File.created_at.desc())
        .all()
    )


def list_all_files(db: Session) -> list[File]:
    return db.query(File).order_by(File.created_at.desc()).all()


def list_public_files(db: Session) -> list[File]:
    return db.query(File).filter(File.file_type == "public").order_by(File.created_at.desc()).all()


def delete_file(file_id: int, db: Session) -> bool:
    file_record = db.query(File).filter(File.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    # Remove physical files
    src = Path(file_record.source_path)
    md = Path(file_record.md_path)
    if src.exists():
        src.unlink()
    if md.exists():
        md.unlink()

    db.delete(file_record)
    db.commit()
    return True
