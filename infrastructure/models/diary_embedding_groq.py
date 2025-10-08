from sqlalchemy import Column, Integer, Text, DateTime, JSON
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from pgvector.sqlalchemy import Vector

class DiaryEmbeddingGroq(Base):
    __tablename__ = "diary_embedding_groq"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    meta_data = Column(JSON)
    embedding = Column(Vector(384))
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), server_default=func.now()) 