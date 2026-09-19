from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText


class SavedSkillResult(Base):
    """Resultado de uma skill (resposta da IA) salvo para um aluno específico."""
    __tablename__ = "saved_skill_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    skill_title: Mapped[str] = mapped_column(String(255), nullable=False)
    response: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    saved_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    saved_by_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
