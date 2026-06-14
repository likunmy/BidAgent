from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(data: ProjectCreate, db: Session) -> Project:
    project = Project(name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def update_project(project_id: int, data: ProjectUpdate, db: Session) -> Project:
    project = get_project(project_id, db)
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    db.commit()
    db.refresh(project)
    return project


def delete_project(project_id: int, db: Session) -> bool:
    project = get_project(project_id, db)
    db.delete(project)
    db.commit()
    return True
