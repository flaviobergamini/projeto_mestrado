"""Processamento dos anexos (PDFs) de um aluno, para o RAG:

    PDF no Storage -> texto extraído (pypdf, sem IA) -> texto ANONIMIZADO (regras, sem IA) -> trechos -> embeddings (Gemini)

Só o texto já anonimizado é guardado (em `student_document_chunks`) e só ele pode chegar ao Gemini, na busca do RAG
quando o usuário marca a fonte "Anexos" no chat ou no PEI. O Gemini é usado aqui APENAS para gerar os embeddings
dos trechos anonimizados; a extração e a anonimização são determinísticas.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select

from core.services.document_anonymizer import anonymize_text, chunk_text
from infrastructure.database_context.database import Database
from infrastructure.models.school import School
from infrastructure.models.student import Student
from infrastructure.models.student_document import (
    DOC_ERROR, DOC_NO_TEXT, DOC_PROCESSING, DOC_READY, StudentDocument, StudentDocumentChunk)
from infrastructure.models.teacher import Teacher
from infrastructure.models.teacher_student_link import TeacherStudentLink
from infrastructure.services.storage_service import StorageService
from infrastructure.utils.pdf_text import PdfTextError, extract_pdf_text

logger = logging.getLogger(__name__)

# processamentos em andamento: guarda a referência das tarefas para o Python não as descartar no meio
_running: set[asyncio.Task] = set()


def schedule_processing(service: "DocumentIngestionService", doc_id: str) -> None:
    """Dispara o processamento em segundo plano (a resposta do upload não espera a vetorização)."""
    task = asyncio.create_task(service.process(doc_id))
    _running.add(task)
    task.add_done_callback(_running.discard)


def _guardian_names(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except Exception:
        items = [raw]
    if not isinstance(items, list):
        items = [items]
    names = []
    for item in items:
        if isinstance(item, dict):
            item = item.get("name") or item.get("nome") or ""
        if isinstance(item, str) and item.strip():
            names.append(item.strip())
    return names


class DocumentIngestionService:
    def __init__(self, database: Database, gemini, usage_repo=None):
        self._db = database
        self._gemini = gemini
        self._usage = usage_repo

    async def _set_status(self, doc_id: str, status: str, detail: Optional[str] = None, chunk_count: int = 0) -> None:
        async with self._db.session() as session:
            doc = await session.get(StudentDocument, doc_id)
            if doc and not doc.deleted:
                doc.status, doc.status_detail, doc.chunk_count = status, detail, chunk_count
                if status in (DOC_READY, DOC_NO_TEXT, DOC_ERROR):
                    doc.processed_at = datetime.utcnow()
                await session.commit()

    async def _identity(self, student_id: str) -> dict:
        """Quem precisa ser anonimizado no texto: o aluno, os responsáveis, a escola e os professores vinculados."""
        async with self._db.session() as session:
            student = await session.get(Student, student_id)
            if not student:
                return {}
            school_name = None
            if student.school_id:
                school = await session.get(School, student.school_id)
                school_name = school.name if school else None
            rows = await session.execute(
                select(Teacher.id, Teacher.name)
                .join(TeacherStudentLink, TeacherStudentLink.teacher_id == Teacher.id)
                .where(TeacherStudentLink.student_id == student_id, TeacherStudentLink.deleted == False))  # noqa: E712
            teachers = [(tid, tname) for tid, tname in rows.all() if tname]
        id_names = {school_name: student.school_id} if school_name and student.school_id else {}
        person_names = {student.name: student.id} if student.name else {}
        person_names.update({name: tid for tid, name in teachers})
        return {
            "id_names": id_names, "person_names": person_names,
            "guardian_names": _guardian_names(student.guardians), "birth_date": student.birth_date,
        }

    def _embed_all(self, chunks: list[str]) -> tuple[list[list[float]], list]:
        vectors, usages = [], []
        for chunk in chunks:
            vector, usage = self._gemini.generate_embedding_tracked(chunk)
            vectors.append(vector)
            usages.append(usage)
        return vectors, usages

    async def process(self, doc_id: str) -> None:
        """Extrai, anonimiza e vetoriza o anexo. Nunca levanta: o resultado fica no `status` do documento."""
        try:
            async with self._db.session() as session:
                doc = await session.get(StudentDocument, doc_id)
                if not doc or doc.deleted:
                    return
                student_id, object_key, caption = doc.student_id, doc.object_key, doc.caption or ""
            await self._set_status(doc_id, DOC_PROCESSING)

            content = await asyncio.to_thread(StorageService().download, object_key)
            text = await asyncio.to_thread(extract_pdf_text, content)
            if not text.strip():
                await self._clear_chunks(doc_id)
                await self._set_status(
                    doc_id, DOC_NO_TEXT, "O PDF não tem texto selecionável (provavelmente é uma imagem digitalizada).")
                return

            identity = await self._identity(student_id)
            anonymized = anonymize_text(text, **identity)
            anonymized_caption = anonymize_text(caption, **identity)
            chunks = chunk_text(anonymized)
            if not chunks:
                await self._clear_chunks(doc_id)
                await self._set_status(doc_id, DOC_NO_TEXT, "Não restou texto aproveitável no PDF.")
                return

            vectors, usages = await asyncio.to_thread(self._embed_all, chunks)
            if self._usage:
                for usage in usages:
                    await self._usage.log(
                        model=usage.model, operation="embedding_document", input_tokens=usage.input_tokens,
                        output_tokens=0, total_tokens=usage.total_tokens, duration_ms=usage.duration_ms)

            async with self._db.session() as session:
                await session.execute(delete(StudentDocumentChunk).where(StudentDocumentChunk.document_id == doc_id))
                for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    session.add(StudentDocumentChunk(
                        document_id=doc_id, student_id=student_id, chunk_index=i, content=chunk, embedding=vector,
                        meta_data={"document_id": doc_id, "caption": anonymized_caption, "chunk": i + 1, "of": len(chunks)}))
                await session.commit()
            await self._set_status(doc_id, DOC_READY, None, len(chunks))
        except PdfTextError as exc:
            await self._set_status(doc_id, DOC_ERROR, str(exc)[:250])
        except Exception:
            logger.exception("Falha ao processar o anexo %s", doc_id)
            await self._set_status(doc_id, DOC_ERROR, "Falha ao vetorizar o documento. Tente reprocessar.")

    async def refresh_caption(self, doc_id: str) -> None:
        """Depois de editar a legenda: atualiza (anonimizada) a legenda guardada nos trechos, sem refazer os embeddings."""
        try:
            async with self._db.session() as session:
                doc = await session.get(StudentDocument, doc_id)
                if not doc or doc.deleted:
                    return
                student_id, caption = doc.student_id, doc.caption or ""
            anonymized = anonymize_text(caption, **await self._identity(student_id))
            async with self._db.session() as session:
                rows = await session.execute(select(StudentDocumentChunk).where(StudentDocumentChunk.document_id == doc_id))
                for chunk in rows.scalars().all():
                    chunk.meta_data = {**(chunk.meta_data or {}), "caption": anonymized}
                await session.commit()
        except Exception:
            logger.exception("Falha ao atualizar a legenda dos trechos do anexo %s", doc_id)

    async def _clear_chunks(self, doc_id: str) -> None:
        async with self._db.session() as session:
            await session.execute(delete(StudentDocumentChunk).where(StudentDocumentChunk.document_id == doc_id))
            await session.commit()
