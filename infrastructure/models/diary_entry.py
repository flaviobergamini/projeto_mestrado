from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    diary_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Structured diary answers — encrypted at rest
    teacher_attention: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    followed_agreements: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    activity_interest: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    had_lunch: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    participated_in_play: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    completed_activities: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    bathroom_use: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)

    open_observation: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    absence_reason: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    teacher_name: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    # presence kept plaintext — used for filtering and RAG logic
    presence: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="diary_entries")
    embeddings: Mapped[list["DiaryEmbeddingGemini"]] = relationship(
        "DiaryEmbeddingGemini", back_populates="diary_entry", cascade="all, delete-orphan"
    )
