from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class AiPrompt(Base):
    __tablename__ = "ai_prompts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # "chat" | "pei"
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="Prompt padrão")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
