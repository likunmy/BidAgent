from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.file import FileDeleteResponse, FileListResponse, FileUploadResponse
from app.services import file_service

router = APIRouter()


@router.post("/public", response_model=FileUploadResponse)
def upload_public_file(
    file: UploadFile,
    display_name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
):
    db_file = file_service.upload_public_file(file, display_name, description, db)
    return db_file


@router.get("", response_model=FileListResponse)
def list_all_files(db: Session = Depends(get_db)):
    files = file_service.list_all_files(db)
    return {"files": files}


@router.get("/public", response_model=FileListResponse)
def list_public_files(db: Session = Depends(get_db)):
    files = file_service.list_public_files(db)
    return {"files": files}


@router.post("/project/{project_id}", response_model=FileUploadResponse)
def upload_project_file(
    project_id: int,
    file: UploadFile,
    display_name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
):
    db_file = file_service.upload_project_file(file, display_name, description, project_id, db)
    return db_file


@router.get("/project/{project_id}", response_model=FileListResponse)
def list_project_files(project_id: int, db: Session = Depends(get_db)):
    files = file_service.list_project_files(project_id, db)
    return {"files": files}


@router.post("/tender/{project_id}", response_model=FileUploadResponse)
def upload_tender_file(
    project_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    db_file = file_service.upload_tender_file(file, project_id, db)
    return db_file


@router.get("/tender/{project_id}")
def get_tender_file(project_id: int, db: Session = Depends(get_db)):
    db_file = file_service.get_tender_file(project_id, db)
    return db_file


@router.delete("/{file_id}", response_model=FileDeleteResponse)
def delete_file(file_id: int, db: Session = Depends(get_db)):
    success = file_service.delete_file(file_id, db)
    return {"success": success}
