import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_type: str
    project_id: int | None
    size: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
