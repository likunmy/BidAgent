from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("/public")
def upload_public_file(file: UploadFile):
    """TODO: upload a public file"""
    return {"filename": file.filename}


@router.get("/public")
def list_public_files():
    """TODO: list all public files"""
    return {"files": []}


@router.post("/project/{project_id}")
def upload_project_file(project_id: int, file: UploadFile):
    """TODO: upload a project-private file"""
    return {"filename": file.filename, "project_id": project_id}


@router.get("/project/{project_id}")
def list_project_files(project_id: int):
    """TODO: list files for a project"""
    return {"files": [], "project_id": project_id}
