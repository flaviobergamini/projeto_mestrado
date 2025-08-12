from sqlalchemy import BigInteger, Date, ForeignKey, Integer, DateTime, String, Text
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped,relationship, mapped_column
from datetime import datetime


class Evaluation(Base):
    __tablename__ = "evaluation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    date: Mapped[datetime] = mapped_column(Date)
    type: Mapped[str] = mapped_column(String(50))
    evaluation_result: Mapped[str] = mapped_column(Text)
    details: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="evaluations")