from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class Skill(Base):
    """Prompt pré-definido, criado pelo admin, que professores/coordenação usam
    no chat pra facilitar tarefas recorrentes (ex: "gere um relatório semanal",
    "me dê ideias sobre X"). Rodar uma skill é apenas enviar `prompt` como
    mensagem de chat — não existe execução/lógica própria (ver api/chat_routes.py)."""
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )
