from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import file_service, project_service

router = APIRouter()


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
