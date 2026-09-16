from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText

if TYPE_CHECKING:
    from infrastructure.models.student import Student
    from infrastructure.models.user_profile import UserProfile


class DiarySummary(Base):
    __tablename__ = "diary_summaries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    author_user_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("user_profiles.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    period_start: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    period_end: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Free-text AI-generated summary — sensitive, encrypted at rest
    summary_text: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)

    # List of {"type": "school"|"family", "id": "...", "date": "..."} — not sensitive, not encrypted
    source_entries: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    student: Mapped[Optional["Student"]] = relationship("Student")
    author: Mapped[Optional["UserProfile"]] = relationship("UserProfile")
