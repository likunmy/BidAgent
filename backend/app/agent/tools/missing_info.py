from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.missing_info import MissingInfo


class MissingItem(BaseModel):
    name: str
    description: str | None = None


class StoreMissingInfoInput(BaseModel):
    project_id: int
    items: list[MissingItem]


class StoreMissingInfoOutput(BaseModel):
    stored: int
    items: list[MissingItem]


def store_missing_info(input_data: StoreMissingInfoInput, db: Session) -> StoreMissingInfoOutput:
    """Store missing info items for a project.

    Clears all existing missing info for the project first, then bulk-inserts
    the new items. This ensures each generation round starts fresh.
    """
    # Clear existing
    db.query(MissingInfo).filter(
        MissingInfo.project_id == input_data.project_id
    ).delete()
    db.flush()

    # Bulk insert
    for item in input_data.items:
        db.add(MissingInfo(
            project_id=input_data.project_id,
            name=item.name,
            description=item.description,
        ))
    db.commit()

    return StoreMissingInfoOutput(
        stored=len(input_data.items),
        items=input_data.items,
    )
