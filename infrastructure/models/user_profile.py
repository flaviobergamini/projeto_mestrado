from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    municipality_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("municipalities.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    school_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("schools.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    teacher_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    municipality: Mapped[Optional["Municipality"]] = relationship("Municipality", back_populates="user_profiles")
    school: Mapped[Optional["School"]] = relationship("School", back_populates="user_profiles")
    teacher: Mapped[Optional["Teacher"]] = relationship("Teacher", back_populates="user_profiles")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession", back_populates="created_by_user", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="user")
