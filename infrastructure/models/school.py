from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base

if TYPE_CHECKING:
    from infrastructure.models.chat_session import ChatSession
    from infrastructure.models.municipality import Municipality
    from infrastructure.models.student import Student
    from infrastructure.models.teacher import Teacher
    from infrastructure.models.user_profile import UserProfile


class School(Base):
    __tablename__ = "schools"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    municipality_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("municipalities.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    institution_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    municipality: Mapped[Optional["Municipality"]] = relationship("Municipality", back_populates="schools")
    teachers: Mapped[list["Teacher"]] = relationship("Teacher", back_populates="school")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="school")
    user_profiles: Mapped[list["UserProfile"]] = relationship("UserProfile", back_populates="school")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="school")
