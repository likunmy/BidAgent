import datetime

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: int
    display_name: str
    description: str | None
    original_name: str
    source_format: str
    size: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    files: list[FileUploadResponse]


class FileDeleteResponse(BaseModel):
    success: bool
