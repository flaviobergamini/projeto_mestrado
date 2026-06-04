from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
import uuid


class TeacherStudentLink(Base):
    __tablename__ = "teacher_student_links"
    __table_args__ = (UniqueConstraint("teacher_id", "student_id", name="uq_tsl_teacher_student"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="student_links")
    student: Mapped["Student"] = relationship("Student", back_populates="teacher_links")
