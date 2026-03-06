from sqlalchemy import BigInteger, ForeignKey, Integer, DateTime
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped, relationship, mapped_column
from datetime import datetime


class UserBeneficiary(Base):
    __tablename__ = "user_beneficiary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    beneficiary_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="beneficiaries")
    beneficiary = relationship("Beneficiary", back_populates="users")
