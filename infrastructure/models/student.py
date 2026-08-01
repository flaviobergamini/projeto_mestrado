from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    school_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("schools.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # age/grade/class_name kept plaintext — used for display grouping, not PII
    age: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    class_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    guardians: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    diagnosis: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    anonymized_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    school: Mapped[Optional["School"]] = relationship("School", back_populates="students")
    teacher_links: Mapped[list["TeacherStudentLink"]] = relationship(
        "TeacherStudentLink", back_populates="student", cascade="all, delete-orphan"
    )
    diary_entries: Mapped[list["DiaryEntry"]] = relationship(
        "DiaryEntry", back_populates="student", cascade="all, delete-orphan"
    )
    pdis: Mapped[list["Pdi"]] = relationship("Pdi", back_populates="student", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="student")
