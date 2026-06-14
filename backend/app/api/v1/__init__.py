from fastapi import APIRouter

from app.api.v1 import files, projects

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
