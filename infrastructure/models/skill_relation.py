from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText

KIND_SKILL, KIND_FIELD = "skill", "field"


class StudentSkillRelation(Base):
    """Relação de uma habilidade (a "mãe") do aluno com OUTRA habilidade ou com um campo de experiência.
    Traz a adaptação, a justificativa e as ações práticas que ligam as duas. Texto sensível: cifrado em repouso."""
    __tablename__ = "student_skill_relations"
    __table_args__ = (Index("ix_student_skill_relations_student_skill", "student_id", "skill_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("bncc_skills.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # "skill" | "field"
    related_skill_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("bncc_skills.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    field_key: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)  # chave de EXPERIENCE_FIELDS
    adaptation: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    actions: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)  # JSON: lista de textos
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="manual", server_default="manual")  # "ai" | "manual"
    created_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class StudentSkillGraph(Base):
    """O grafo de relações de uma habilidade finalística do aluno, guardado como UM documento JSON (cifrado em repouso).

    É a fonte única: a tela é desenhada a partir dele e qualquer análise da IA parte dele (anonimizado). Guarda só a
    ESTRUTURA (quem se relaciona com quem, direção, motivo, posição); estrelas e observações vêm sempre das notas do aluno.
    `revision` sobe a cada atualização (controle de concorrência)."""
    __tablename__ = "student_skill_graphs"

    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("bncc_skills.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    document: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    updated_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
