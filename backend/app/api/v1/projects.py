from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_projects():
    """TODO: list all projects"""
    return {"projects": []}


@router.post("")
def create_project():
    """TODO: create a new project"""
    return {"message": "not implemented"}


@router.get("/{project_id}")
def get_project(project_id: int):
    """TODO: get project by id"""
    return {"project_id": project_id}


@router.put("/{project_id}")
def update_project(project_id: int):
    """TODO: update project"""
    return {"project_id": project_id}


@router.delete("/{project_id}")
def delete_project(project_id: int):
    """TODO: delete project"""
    return {"project_id": project_id}
