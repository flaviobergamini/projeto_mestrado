from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base

if TYPE_CHECKING:
    from infrastructure.models.chat_session import ChatSession
    from infrastructure.models.school import School
    from infrastructure.models.teacher_student_link import TeacherStudentLink
    from infrastructure.models.user_profile import UserProfile


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
    # Métricas de composição do corpo docente (painel administrativo) — plaintext
    # e em listas fixas (ver core/constants/demographics.py) para permitir GROUP BY
    # direto via SQL. birth_year (não a data completa) reduz a sensibilidade do
    # dado mantendo a granularidade necessária pro cálculo de faixa etária.
    birth_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    teacher_role: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    school: Mapped[Optional["School"]] = relationship("School", back_populates="teachers")
    student_links: Mapped[list["TeacherStudentLink"]] = relationship(
        "TeacherStudentLink", back_populates="teacher", cascade="all, delete-orphan"
    )
    user_profiles: Mapped[list["UserProfile"]] = relationship("UserProfile", back_populates="teacher")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="teacher")
