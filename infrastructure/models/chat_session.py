from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Date, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    created_by_user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("user_profiles.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    created_by_username: Mapped[str] = mapped_column(String(120), nullable=False)
    created_by_role: Mapped[str] = mapped_column(String(64), nullable=False)
    municipality_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("municipalities.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    school_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("schools.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    teacher_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True
    )
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    student_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    school_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    created_by_user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="chat_sessions")
    municipality: Mapped[Optional["Municipality"]] = relationship("Municipality", back_populates="chat_sessions")
    school: Mapped[Optional["School"]] = relationship("School", back_populates="chat_sessions")
    teacher: Mapped[Optional["Teacher"]] = relationship("Teacher", back_populates="chat_sessions")
    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
