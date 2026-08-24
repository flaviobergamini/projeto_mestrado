import uuid
import asyncio
import httpx
from datetime import date as _date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.storage_service import StorageService
from infrastructure.services.rag_service import RagService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.pdf_service import generate_diary_pdf

router = APIRouter(prefix="/diary", tags=["Diary"])


class DiaryEntryCreate(BaseModel):
    student_id: str
    diary_date: str
    presence: Optional[str] = "Presente"
    teacher_name: Optional[str] = None
    teacher_attention: Optional[str] = None
    followed_agreements: Optional[str] = None
    activity_interest: Optional[str] = None
    had_lunch: Optional[str] = None
    participated_in_play: Optional[str] = None
    completed_activities: Optional[str] = None
    bathroom_use: Optional[str] = None
    open_observation: Optional[str] = None
    absence_reason: Optional[str] = None


class DiaryEntryUpdate(BaseModel):
    diary_date: Optional[str] = None
    presence: Optional[str] = None
    teacher_name: Optional[str] = None
    teacher_attention: Optional[str] = None
    followed_agreements: Optional[str] = None
    activity_interest: Optional[str] = None
    had_lunch: Optional[str] = None
    participated_in_play: Optional[str] = None
    completed_activities: Optional[str] = None
    bathroom_use: Optional[str] = None
    open_observation: Optional[str] = None
    absence_reason: Optional[str] = None


ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/webm;codecs=opus", "audio/ogg", "audio/ogg;codecs=opus",
    "audio/mp4", "audio/mpeg", "audio/wav", "audio/x-wav",
}
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/transcribe-audio")
@inject
async def transcribe_diary_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_read_write),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
):
    """Receive an audio recording and return pre-filled diary fields extracted by Gemini."""
    content_type = (file.content_type or "").split(";")[0].strip()
    normalized_mime = content_type if content_type in {
        "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/wav", "audio/x-wav",
    } else "audio/webm"

    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Áudio muito grande. Máximo: 20 MB.")

    try:
        fields, usage = await asyncio.to_thread(
            gemini.transcribe_diary_audio, content, mime_type=normalized_mime
        )
        await usage_repo.log(
            model=usage.model,
            operation="diary_audio_transcription",
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            duration_ms=usage.duration_ms,
            user_id=current_user.get("user_id"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao transcrever áudio: {str(e)}")

    return fields


@router.get("/students")
@inject
async def list_students_with_diary(
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    return await repo.list_students_with_diary()


@router.get("/student/{student_id}/teachers")
@inject
async def get_linked_teachers(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    """Returns teacher names linked to the student (for the diary form)."""
    return await repo.get_linked_teachers(student_id)


@router.get("/student/{student_id}")
@inject
async def list_entries(
    student_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    return await repo.list_by_student(
        student_id,
        source="school",
        date_from=_date.fromisoformat(date_from) if date_from else None,
        date_to=_date.fromisoformat(date_to) if date_to else None,
    )


@router.get("/{entry_id}")
@inject
async def get_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    entry = await repo.get_by_id(entry_id)
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado")
    
    return entry


async def _trigger_embedding(rag: RagService, student_repo: StudentRepository, entry: dict) -> None:
    """Fire-and-forget: embed diary entry (anonymised — no student name sent to Gemini)."""
    try:
        await rag.embed_diary_entry(entry)
    except Exception:
        pass  # never let embedding failure surface to the caller


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_entry(
    body: DiaryEntryCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
):
    data = body.model_dump()
    if not data.get("teacher_name"):
        data["teacher_name"] = current_user.get("full_name") or current_user.get("username", "")

    entry = await repo.create(data)
    asyncio.create_task(_trigger_embedding(rag, student_repo, entry))
    return entry


@router.put("/{entry_id}")
@inject
async def update_entry(
    entry_id: str,
    body: DiaryEntryUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
):
    updated = await repo.update(entry_id, body.model_dump(exclude_none=True))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado")

    asyncio.create_task(_trigger_embedding(rag, student_repo, updated))
    return updated


@router.delete("/student/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_all_for_student(
    student_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    await repo.delete_all_for_student(student_id)


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _fetch_images_map(entry_ids: list[str], diary_repo: DiaryRepository) -> dict[str, list[bytes]]:
    """Download image bytes for a list of diary entry IDs."""
    if not entry_ids:
        return {}
    grouped = await diary_repo.list_images_batch(entry_ids)
    all_keys = [rec["object_key"] for recs in grouped.values() for rec in recs if rec.get("object_key")]
    if not all_keys:
        return {}
    storage = StorageService()
    signed_map = await storage.create_signed_urls_batch_async(all_keys)
    result: dict[str, list[bytes]] = {}
    async with httpx.AsyncClient(timeout=30) as client:
        for entry_id, recs in grouped.items():
            imgs: list[bytes] = []
            for rec in recs:
                url = signed_map.get(rec.get("object_key", "")) or rec.get("public_url", "")
                if url:
                    try:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            imgs.append(resp.content)
                    except Exception:
                        pass
            if imgs:
                result[entry_id] = imgs
    return result


# ── Image routes ──────────────────────────────────────────────────────────────

@router.get("/export/pdf/{student_id}")
@inject
async def export_diary_pdf(
    student_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    """Exporta os registros do diário escolar de um aluno em PDF com timbragem."""
    student = await student_repo.get_by_id(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")

    entries = await repo.list_by_student(
        student_id,
        source="school",
        date_from=_date.fromisoformat(date_from) if date_from else None,
        date_to=_date.fromisoformat(date_to) if date_to else None,
    )

    entry_ids = [e["id"] for e in entries if e.get("id")]
    images_map = await _fetch_images_map(entry_ids, repo)

    pdf_bytes = generate_diary_pdf(
        entries=entries,
        student_name=student.get("name", ""),
        diary_label="Diário Escolar",
        date_from=date_from,
        date_to=date_to,
        source="school",
        images_map=images_map,
    )

    safe_name = (student.get("name") or "aluno").replace(" ", "_")[:40]
    filename = f"Diario_Escolar_{safe_name}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/{entry_id}/images", status_code=status.HTTP_201_CREATED)
@inject
async def upload_image(
    entry_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    entry = await repo.get_by_id(entry_id)

    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Tipo de arquivo não permitido. Use JPEG, PNG, GIF ou WebP.")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Imagem muito grande. Máximo permitido: 10 MB.")

    ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
    object_key = f"diary/{entry_id}/{uuid.uuid4()}.{ext}"

    storage = StorageService()

    public_url = storage.upload(object_key, content, file.content_type)

    return await repo.add_image(
        entry_id=entry_id,
        bucket=storage.bucket,
        object_key=object_key,
        original_filename=file.filename or object_key,
        mime_type=file.content_type,
        size_bytes=len(content),
        public_url=public_url,
    )


@router.get("/images/batch")
@inject
async def list_images_batch(
    entry_ids: str,  # comma-separated list of entry IDs
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    """Return images for multiple diary entries in one request, with batch-signed URLs."""
    ids = [i.strip() for i in entry_ids.split(",") if i.strip()]
    if not ids:
        return {}

    grouped = await repo.list_images_batch(ids)

    # Collect all object keys then sign them in one Supabase call
    all_keys = [rec["object_key"] for recs in grouped.values() for rec in recs if rec.get("object_key")]
    storage = StorageService()
    signed_map = await storage.create_signed_urls_batch_async(all_keys) if all_keys else {}

    for recs in grouped.values():
        for rec in recs:
            key = rec.get("object_key", "")
            rec["url"] = signed_map.get(key) or rec.get("public_url", "")

    return grouped


@router.get("/{entry_id}/images")
@inject
async def list_images(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    records = await repo.list_images(entry_id)
    if not records:
        return records

    storage = StorageService()
    keys = [r["object_key"] for r in records if r.get("object_key")]
    signed_map = await storage.create_signed_urls_batch_async(keys) if keys else {}
    for rec in records:
        rec["url"] = signed_map.get(rec.get("object_key", "")) or rec.get("public_url", "")
    return records


@router.delete("/images/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_image(
    file_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    record = await repo.delete_image(file_id)

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")

    storage = StorageService()
    storage.delete(record["object_key"])


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    deleted = await repo.delete(entry_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado")
