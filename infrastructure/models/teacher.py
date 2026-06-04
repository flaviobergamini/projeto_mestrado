from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    school_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("schools.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    school: Mapped[Optional["School"]] = relationship("School", back_populates="teachers")
    student_links: Mapped[list["TeacherStudentLink"]] = relationship(
        "TeacherStudentLink", back_populates="teacher", cascade="all, delete-orphan"
    )
    user_profiles: Mapped[list["UserProfile"]] = relationship("UserProfile", back_populates="teacher")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="teacher")
