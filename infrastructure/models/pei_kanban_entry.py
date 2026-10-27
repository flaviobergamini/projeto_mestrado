from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, SmallInteger, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class PeiKanbanEntry(Base):
    """Lançamento do diário de uma ação (card): uma execução da ação, com data, texto e fotos.

    A ação pode ser executada várias vezes até ser concluída; cada vez vira um lançamento."""
    __tablename__ = "pei_kanban_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    card_id: Mapped[str] = mapped_column(String(64), ForeignKey("pei_kanban_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    reaction: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)  # reação do aluno nesta execução (1 a 5)
    photos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list de object keys no storage
    created_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
