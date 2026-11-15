from datetime import datetime
from typing import Optional
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base

# estado do processamento (extração de texto -> anonimização -> vetorização)
DOC_PENDING, DOC_PROCESSING, DOC_READY, DOC_NO_TEXT, DOC_ERROR = "pending", "processing", "ready", "no_text", "error"


class StudentDocument(Base):
    """Anexo (PDF) de um aluno, guardado no Supabase Storage. A legenda identifica o documento nas telas."""
    __tablename__ = "student_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    caption: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=DOC_PENDING, server_default=DOC_PENDING)
    status_detail: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class StudentDocumentChunk(Base):
    """Trecho ANONIMIZADO de um anexo, com o embedding usado na busca do RAG (o texto original não é guardado aqui)."""
    __tablename__ = "student_document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("student_documents.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    embedding = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
