from sqlalchemy import BigInteger, Date, ForeignKey, Integer, DateTime, String, Text
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped,relationship, mapped_column
from datetime import date, datetime
from typing import Optional


class TherapeuticSessions(Base):
    __tablename__ =  "therapeutic_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    therapeutic_plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("therapeutic_plan.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    professional_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("professional.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    clinic_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("clinic.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    session_date: Mapped[datetime] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text)
    observation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    therapeutic_plan = relationship("TherapeuticPlan", back_populates="sessions")
    professional = relationship("Professional", back_populates="sessions")
    clinic = relationship("Clinic", back_populates="sessions")