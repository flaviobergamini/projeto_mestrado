from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class GeneratedPei(Base):
    __tablename__ = "generated_peis"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    student_name: Mapped[str] = mapped_column(String(120), nullable=False)
    pei_text: Mapped[str] = mapped_column(Text, nullable=False)
    sources_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    generated_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
