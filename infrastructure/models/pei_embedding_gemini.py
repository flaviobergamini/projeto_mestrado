from sqlalchemy import Column, Integer, Text, DateTime, JSON, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from infrastructure.database_context.database import Base
from pgvector.sqlalchemy import Vector


class PdiEmbeddingGemini(Base):
    __tablename__ = "pdi_embedding_gemini"

    id = Column(Integer, primary_key=True, index=True)
    pdi_id = Column(String(64), ForeignKey("pdis.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    student_id = Column(String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON)
    embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pdi = relationship("Pdi", back_populates="embeddings")
