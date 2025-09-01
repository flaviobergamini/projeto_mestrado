from sqlalchemy import BigInteger, Date, ForeignKey, Integer, DateTime, String, Text
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped,relationship, mapped_column
from datetime import datetime


class TherapeuticPlan(Base):
    __tablename__ = "therapeutic_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    objective: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    workload: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="therapeutic_plans")
    sessions = relationship("TherapeuticSessions", back_populates="therapeutic_plan", cascade="all, delete-orphan")