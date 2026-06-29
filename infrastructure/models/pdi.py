from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base


class Pdi(Base):
    __tablename__ = "pdis"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    birth_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    class_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    guardians: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    teacher_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="pdis")
    trimester_subjects: Mapped[list["PdiTrimesterSubject"]] = relationship(
        "PdiTrimesterSubject", back_populates="pdi", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list["PdiEmbeddingGemini"]] = relationship(
        "PdiEmbeddingGemini", back_populates="pdi", cascade="all, delete-orphan"
    )
