from sqlalchemy import ForeignKey, Integer, DateTime, String, Text
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped,relationship, mapped_column
from datetime import date, datetime
from typing import Optional


class Beneficiary(Base):
    __tablename__ = "beneficiary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[Optional[date]]
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    main_responsible: Mapped[Optional[str]] = mapped_column(String(100))
    responsible_contact: Mapped[Optional[str]] = mapped_column(String(100))
    entry_date: Mapped[Optional[date]]
    exit_date: Mapped[Optional[date]]
    status: Mapped[Optional[str]] = mapped_column(String(10))
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("school.id", onupdate="CASCADE", ondelete="CASCADE"))
    healthplan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("health_plan.id", onupdate="CASCADE", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    audits = relationship("Audit", back_populates="beneficiary", cascade="all, delete-orphan")
    clinics = relationship("BeneficiaryClinic", back_populates="beneficiary", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="beneficiary", cascade="all, delete-orphan")
    family_reunions = relationship("FamilyReunion", back_populates="beneficiary", cascade="all, delete-orphan")
    school_feedbacks = relationship("SchoolFeedback", back_populates="beneficiary", cascade="all, delete-orphan")
    therapeutic_plans = relationship("TherapeuticPlan", back_populates="beneficiary", cascade="all, delete-orphan")
    diaries = relationship("Diary", back_populates="beneficiary", cascade="all, delete-orphan")
    users = relationship("UserBeneficiary", back_populates="beneficiary", cascade="all, delete-orphan")
