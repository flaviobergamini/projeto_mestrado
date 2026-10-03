from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText


class FunctionalProfile(Base):
    __tablename__ = "functional_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    origin: Mapped[str] = mapped_column(String(10), nullable=False, default="manual", server_default="manual")  # ai | manual
    sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: fontes usadas na geração
    content: Mapped[str] = mapped_column(EncryptedText, nullable=False)  # JSON normalizado (criptografado)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_by_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    edited_by_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
