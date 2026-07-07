import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.services.storage_service import StorageService

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
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    return await repo.list_by_student(student_id)


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


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_entry(
    body: DiaryEntryCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    data = body.model_dump()
    # If teacher_name not provided by frontend, fall back to logged user
    if not data.get("teacher_name"):
        data["teacher_name"] = current_user.get("full_name") or current_user.get("username", "")

    return await repo.create(data)


@router.put("/{entry_id}")
@inject
async def update_entry(
    entry_id: str,
    body: DiaryEntryUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    updated = await repo.update(entry_id, body.model_dump(exclude_none=True))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado")
    
    return updated


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


@router.delete("/student/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_all_for_student(
    student_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    await repo.delete_all_for_student(student_id)


# ── Image routes ──────────────────────────────────────────────────────────────

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


@router.get("/{entry_id}/images")
@inject
async def list_images(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    records = await repo.list_images(entry_id)
    storage = StorageService()
    for rec in records:
        signed = storage.create_signed_url(rec["object_key"])
        rec["url"] = signed or rec.get("public_url", "")
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
