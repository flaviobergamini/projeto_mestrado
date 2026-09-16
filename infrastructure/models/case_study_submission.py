from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText, EncryptedJSON

if TYPE_CHECKING:
    from infrastructure.models.student import Student


class CaseStudySubmission(Base):
    __tablename__ = "case_study_submissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True
    )
    submitted_by: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    answers: Mapped[Optional[dict]] = mapped_column(EncryptedJSON, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, name="metadata")
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    student: Mapped[Optional["Student"]] = relationship("Student")
