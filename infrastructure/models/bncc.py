from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, SmallInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText


class BnccSkill(Base):
    """Habilidade BNCC (código alfanumérico + descrição), por ano."""
    __tablename__ = "bncc_skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)  # infantil | fundamental
    grade: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    grade_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    area: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class StudentSkillScore(Base):
    """Nota 0-5 (e observação) de um aluno em uma habilidade. Sem linha = nota 0."""
    __tablename__ = "student_skill_scores"

    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
    skill_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("bncc_skills.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True, index=True
    )
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")
    observation: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    updated_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_by_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SkillReport(Base):
    """Relatório de habilidades BNCC de um aluno, guardado como JSON (criptografado)."""
    __tablename__ = "skill_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_by_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
