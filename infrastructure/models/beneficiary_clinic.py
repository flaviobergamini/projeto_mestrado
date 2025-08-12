from sqlalchemy import BigInteger, Date, ForeignKey, Integer, DateTime
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped,relationship, mapped_column
from datetime import datetime


class BeneficiaryClinic(Base):
    __tablename__ = "beneficiary_clinic"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    clinic_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("clinic.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    beneficiary = relationship("Beneficiary", back_populates="clinics")
    clinic = relationship("Clinic", back_populates="beneficiaries")