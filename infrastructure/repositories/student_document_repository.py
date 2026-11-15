"""Anexos (PDFs) dos alunos."""
import uuid
from typing import Optional
from sqlalchemy import delete, select

from infrastructure.database_context.database import Database
from infrastructure.models.school import School
from infrastructure.models.student import Student
from infrastructure.models.student_document import StudentDocument, StudentDocumentChunk


def _doc_dict(d: StudentDocument) -> dict:
    return {
        "doc_id": d.id, "student_id": d.student_id, "caption": d.caption or "", "file_name": d.original_filename,
        "size_bytes": d.size_bytes, "upload_date": d.created_at.isoformat() if d.created_at else None,
        "status": d.status, "status_detail": d.status_detail, "chunk_count": d.chunk_count,
    }


class StudentDocumentRepository:
    def __init__(self, database: Database):
        self._db = database

    async def list_grouped(self, scope=None) -> list[dict]:
        """Alunos (no escopo do usuário) que têm anexos, cada um com a lista de documentos."""
        async with self._db.session() as session:
            rows = await session.execute(
                select(StudentDocument, Student)
                .join(Student, Student.id == StudentDocument.student_id)
                .where(StudentDocument.deleted == False, Student.deleted == False,  # noqa: E712
                       *([scope] if scope is not None else []))
                .order_by(StudentDocument.created_at)
            )
            pairs = rows.all()
            school_ids = {s.school_id for _, s in pairs if s.school_id}
            schools = {}
            if school_ids:
                res = await session.execute(select(School).where(School.id.in_(school_ids)))
                schools = {sc.id: sc.name for sc in res.scalars().all()}
        grouped: dict[str, dict] = {}
        for doc, student in pairs:
            g = grouped.setdefault(student.id, {
                "student_id": student.id, "student_name": student.name or "",
                "school": schools.get(student.school_id, ""), "documents": [],
            })
            g["documents"].append(_doc_dict(doc))
        out = list(grouped.values())
        for g in out:
            g["document_count"] = len(g["documents"])
        return sorted(out, key=lambda g: g["student_name"].lower())

    async def get(self, doc_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            d = await session.get(StudentDocument, doc_id)
            if not d or d.deleted:
                return None
            return {**_doc_dict(d), "object_key": d.object_key, "mime_type": d.mime_type}

    async def add(self, *, student_id: str, caption: str, filename: str, mime_type: str, size_bytes: int,
                  bucket: str, object_key: str, uploaded_by: Optional[str], doc_id: Optional[str] = None) -> dict:
        async with self._db.session() as session:
            d = StudentDocument(
                id=doc_id or str(uuid.uuid4()), student_id=student_id, caption=caption, original_filename=filename,
                mime_type=mime_type, size_bytes=size_bytes, bucket=bucket, object_key=object_key, uploaded_by=uploaded_by)
            session.add(d)
            await session.commit()
            await session.refresh(d)
            return _doc_dict(d)

    async def set_caption(self, doc_id: str, caption: str) -> Optional[dict]:
        async with self._db.session() as session:
            d = await session.get(StudentDocument, doc_id)
            if not d or d.deleted:
                return None
            d.caption = caption
            await session.commit()
            await session.refresh(d)
            return _doc_dict(d)

    async def delete(self, doc_id: str) -> Optional[str]:
        """Marca como apagado; devolve a chave do arquivo no storage (para remover), ou None se não existia."""
        async with self._db.session() as session:
            d = await session.get(StudentDocument, doc_id)
            if not d or d.deleted:
                return None
            d.deleted = True
            key = d.object_key
            # os trechos vetorizados saem junto: o anexo apagado não pode mais aparecer no RAG
            await session.execute(delete(StudentDocumentChunk).where(StudentDocumentChunk.document_id == doc_id))
            await session.commit()
            return key
