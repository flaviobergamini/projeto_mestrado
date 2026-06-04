from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class SchoolRegistrationSubmission(Base):
    __tablename__ = "school_registration_submissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, name="metadata")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=None, nullable=False)
