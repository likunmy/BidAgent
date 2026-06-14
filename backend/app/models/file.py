import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="前端填写的展示名，也是MD文件名")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文件简介")
    original_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始上传文件名")
    source_format: Mapped[str] = mapped_column(String(10), nullable=False, comment="pdf | docx | txt")
    source_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="data/下的源文件路径")
    md_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="uploads/public/下的MD文件路径")
    file_type: Mapped[str] = mapped_column(String(20), nullable=False, default="public", comment="public | project")
    size: Mapped[int] = mapped_column(default=0, comment="文件大小(bytes)")
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
