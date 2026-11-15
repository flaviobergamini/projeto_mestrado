"""Anexos (PDFs) dos alunos: enviar, listar por aluno, editar a legenda, baixar e apagar."""
import asyncio
import uuid
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from api.dependencies import get_current_user, get_current_user_read_write
from api.student_access import ensure_student_access, student_scope_condition
from core.kernel.container import Container
from infrastructure.database_context.database import Database
from infrastructure.repositories.student_document_repository import StudentDocumentRepository
from infrastructure.services.document_ingestion import DocumentIngestionService, schedule_processing
from infrastructure.services.storage_service import StorageService

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB
NOT_FOUND = "Documento não encontrado"


class CaptionBody(BaseModel):
    caption: str = Field(default="", max_length=255)


def _is_pdf(file: UploadFile, content: bytes) -> bool:
    return content[:5] == b"%PDF-" and (file.content_type or "").lower() in ("application/pdf", "application/x-pdf", "application/octet-stream")


async def _doc_or_404(repo: StudentDocumentRepository, database: Database, user: dict, doc_id: str) -> dict:
    """O documento, se existir e o aluno dele for do usuário (senão 404, sem revelar que existe)."""
    doc = await repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    await ensure_student_access(database, user, doc["student_id"])
    return doc


@router.get("/students")
@inject
async def list_students_with_documents(
    current_user: dict = Depends(get_current_user),
    repo: StudentDocumentRepository = Depends(Provide[Container.student_document_repository]),
):
    """Alunos do usuário que têm anexos, cada um com a lista de documentos."""
    return await repo.list_grouped(student_scope_condition(current_user))


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@inject
async def upload_document(
    student_id: str = Form(...),
    caption: str = Form(""),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_read_write),
    repo: StudentDocumentRepository = Depends(Provide[Container.student_document_repository]),
    database: Database = Depends(Provide[Container.database]),
    ingestion: DocumentIngestionService = Depends(Provide[Container.document_ingestion_service]),
):
    await ensure_student_access(database, current_user, student_id)
    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PDF muito grande. Máximo permitido: 20 MB.")
    if not _is_pdf(file, content):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Envie um arquivo PDF válido.")

    doc_id = str(uuid.uuid4())
    object_key = f"student-documents/{student_id}/{doc_id}.pdf"
    storage = StorageService()
    await asyncio.to_thread(storage.upload, object_key, content, "application/pdf")
    created = await repo.add(
        student_id=student_id, caption=caption.strip()[:255], filename=(file.filename or "documento.pdf")[:255],
        mime_type="application/pdf", size_bytes=len(content), bucket=storage.bucket, object_key=object_key,
        uploaded_by=current_user.get("user_id"), doc_id=doc_id,
    )
    schedule_processing(ingestion, doc_id)  # extrai, anonimiza e vetoriza em segundo plano
    return created


@router.patch("/{doc_id}/caption")
@inject
async def update_caption(
    doc_id: str,
    body: CaptionBody,
    current_user: dict = Depends(get_current_user_read_write),
    repo: StudentDocumentRepository = Depends(Provide[Container.student_document_repository]),
    database: Database = Depends(Provide[Container.database]),
    ingestion: DocumentIngestionService = Depends(Provide[Container.document_ingestion_service]),
):
    await _doc_or_404(repo, database, current_user, doc_id)
    updated = await repo.set_caption(doc_id, body.caption.strip())
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    await ingestion.refresh_caption(doc_id)
    return updated


@router.post("/{doc_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
@inject
async def reprocess_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: StudentDocumentRepository = Depends(Provide[Container.student_document_repository]),
    database: Database = Depends(Provide[Container.database]),
    ingestion: DocumentIngestionService = Depends(Provide[Container.document_ingestion_service]),
):
    """Refaz a extração, a anonimização e a vetorização (ex.: depois de uma falha, ou de mudar o nome do aluno)."""
    await _doc_or_404(repo, database, current_user, doc_id)
    schedule_processing(ingestion, doc_id)
    return {"doc_id": doc_id, "status": "processing"}


@router.get("/{doc_id}/download")
@inject
async def download_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    repo: StudentDocumentRepository = Depends(Provide[Container.student_document_repository]),
    database: Database = Depends(Provide[Container.database]),
):
    doc = await _doc_or_404(repo, database, current_user, doc_id)
    try:
        data = await asyncio.to_thread(StorageService().download, doc["object_key"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Não foi possível obter o arquivo do armazenamento.")
    return Response(content=data, media_type=doc["mime_type"])


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: StudentDocumentRepository = Depends(Provide[Container.student_document_repository]),
    database: Database = Depends(Provide[Container.database]),
):
    await _doc_or_404(repo, database, current_user, doc_id)
    key: Optional[str] = await repo.delete(doc_id)
    if key:
        await asyncio.to_thread(StorageService().delete, key)
