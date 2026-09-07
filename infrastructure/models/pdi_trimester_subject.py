from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
import uuid

if TYPE_CHECKING:
    from infrastructure.models.pdi import Pdi


class PdiTrimesterSubject(Base):
    __tablename__ = "pdi_trimester_subjects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    pdi_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("pdis.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    trimester: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adaptations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learnings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    pdi: Mapped["Pdi"] = relationship("Pdi", back_populates="trimester_subjects")
