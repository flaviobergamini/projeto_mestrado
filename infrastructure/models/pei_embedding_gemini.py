from sqlalchemy import Column, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from pgvector.sqlalchemy import Vector


class PEIEmbeddingGemini(Base):
    __tablename__ = "pei_embedding_gemini"

    id = Column(Integer, primary_key=True, index=True)
    pei_id = Column(Integer, ForeignKey("pei.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    beneficiary_id = Column(Integer, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)

    # Conteúdo textual do chunk do PEI
    content = Column(Text, nullable=False)

    # Metadata adicional (ex: seção do PEI, página, etc)
    meta_data = Column(JSON)

    # Embedding vetorial gerado pelo Gemini
    embedding = Column(Vector(768))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
