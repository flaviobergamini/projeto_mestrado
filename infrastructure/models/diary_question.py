from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class DiaryQuestion(Base):
    __tablename__ = "diary_questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # NULL = pergunta padrão (vale para todo aluno sem lista própria)
    student_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # True = a resposta vai para a coluna de mesmo nome em diary_entries
    builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
