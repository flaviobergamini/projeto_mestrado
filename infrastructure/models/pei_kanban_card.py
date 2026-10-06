from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, SmallInteger, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class PeiKanbanCard(Base):
    """Card do quadro de execução do PEI (A fazer / Fazendo / Concluído), por aluno.

    Criado automaticamente (um card por seção) sempre que um PEI é gerado, e também
    manualmente pelo professor. Alimenta de volta a geração de PEI/chat via a fonte
    'kanban_progress' (ver AnonymizationService.build_context)."""
    __tablename__ = "pei_kanban_cards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    pei_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("generated_peis.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo", server_default="todo")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual", server_default="manual")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    skill_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("bncc_skills.id", ondelete="SET NULL"), nullable=True, index=True)
    adaptation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    daily_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correlated_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list de códigos
    score_at_creation: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
