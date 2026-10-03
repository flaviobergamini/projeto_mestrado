from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class UserSchool(Base):
    __tablename__ = "user_schools"

    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("user_profiles.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True
    )
    school_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("schools.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
