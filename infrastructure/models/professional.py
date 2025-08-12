from sqlalchemy import ForeignKey, Integer, DateTime, String
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional


class Professional(Base):
    __tablename__ = "professional"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    function: Mapped[Optional[str]] = mapped_column(String(50))
    specialty: Mapped[Optional[str]] = mapped_column(String(100))
    contact: Mapped[Optional[str]] = mapped_column(String(100))
    availability: Mapped[Optional[str]] = mapped_column(String(100))
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinic.id", onupdate="CASCADE", ondelete="CASCADE"))
    email: Mapped[Optional[str]] = mapped_column(String(50))
    password: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    clinic = relationship("Clinic", back_populates="professionals")