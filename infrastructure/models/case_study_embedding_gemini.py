from sqlalchemy import Column, Integer, Text, DateTime, JSON, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from infrastructure.database_context.database import Base
from pgvector.sqlalchemy import Vector


class CaseStudyEmbeddingGemini(Base):
    __tablename__ = "case_study_embedding_gemini"

    id = Column(Integer, primary_key=True, index=True)
    case_study_id = Column(String(64), ForeignKey("case_study_submissions.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    student_id = Column(String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
