from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
import uuid


class TherapistStudentLink(Base):
    __tablename__ = "therapist_student_links"
    __table_args__ = (UniqueConstraint("therapist_user_id", "student_id", name="uq_thl_therapist_student"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    therapist_user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("user_profiles.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
