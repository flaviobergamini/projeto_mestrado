from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base


class Municipality(Base):
    __tablename__ = "municipalities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    schools: Mapped[list["School"]] = relationship("School", back_populates="municipality")
    user_profiles: Mapped[list["UserProfile"]] = relationship("UserProfile", back_populates="municipality")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="municipality")
