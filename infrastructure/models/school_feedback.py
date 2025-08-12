from sqlalchemy import BigInteger, Date, ForeignKey, Integer, DateTime, String, Text
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped,relationship, mapped_column
from datetime import datetime


class SchoolFeedback(Base):
    __tablename__ = "school_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    supervisor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("supervisor.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    feedback_date: Mapped[datetime] = mapped_column(Date)
    observation: Mapped[str] = mapped_column(Text)
    tracking_status: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="school_feedbacks")
    supervisor = relationship("Supervisor", back_populates="school_feedbacks")