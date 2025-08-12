from sqlalchemy import BigInteger, Date, ForeignKey, Integer, DateTime, String, Text
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped,relationship, mapped_column
from datetime import datetime


class Audit(Base):
    __tablename__ = "audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    supervisor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("supervisor.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    audit_date: Mapped[datetime] = mapped_column(Date)
    details: Mapped[str] = mapped_column(Text)
    conclusion: Mapped[str] = mapped_column(Text)
    next_audit: Mapped[datetime] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="audits")
    supervisor = relationship("Supervisor", back_populates="audits")