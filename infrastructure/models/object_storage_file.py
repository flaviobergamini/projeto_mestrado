from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class ObjectStorageFile(Base):
    __tablename__ = "object_storage_files"
    __table_args__ = (UniqueConstraint("doc_type", "reference_id", name="uq_object_storage_doc_ref"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(128), nullable=False)
    bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
