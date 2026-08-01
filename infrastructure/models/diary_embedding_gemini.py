from sqlalchemy import Column, Integer, Text, DateTime, JSON, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from infrastructure.database_context.database import Base
from pgvector.sqlalchemy import Vector


class DiaryEmbeddingGemini(Base):
    __tablename__ = "diary_embedding_gemini"

    id = Column(Integer, primary_key=True, index=True)
    diary_entry_id = Column(String(64), ForeignKey("diary_entries.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True)
    student_id = Column(String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True)
    content = Column(Text)
    meta_data = Column(JSON)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    diary_entry = relationship("DiaryEntry", back_populates="embeddings")
