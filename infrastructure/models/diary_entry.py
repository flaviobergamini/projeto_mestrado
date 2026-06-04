from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    diary_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Structured diary answers (Yes / No / Partially)
    teacher_attention: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    followed_agreements: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    activity_interest: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    had_lunch: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    participated_in_play: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    completed_activities: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bathroom_use: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    open_observation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
