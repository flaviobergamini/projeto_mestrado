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
    adaptation: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    actions: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    correlated_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list de códigos
    ai_excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    in_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    plan_ai_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_by_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class StudentSkillEvent(Base):
    """Histórico de uma habilidade de um aluno (mudança de nota, marcos do plano)."""
    __tablename__ = "student_skill_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("bncc_skills.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)  # score | plan | ai_plan | ai_suggestion
    old_score: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    new_score: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_card_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SkillSuggestion(Base):
    """Sugestão da IA (rodada 2) de alterar a nota; a professora aceita ou recusa."""
    __tablename__ = "skill_suggestions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("bncc_skills.id", ondelete="CASCADE"), nullable=False)
    current_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    suggested_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_card_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending", server_default="pending")
    decided_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SkillMonthlySnapshot(Base):
    """Memória de médio prazo: resumo mensal da evolução de uma habilidade."""
    __tablename__ = "skill_monthly_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(64), ForeignKey("bncc_skills.id", ondelete="CASCADE"), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    end_score: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


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
