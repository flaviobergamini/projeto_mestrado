from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.diary_repository import DiaryRepository

router = APIRouter(prefix="/diary", tags=["Diary"])


class DiaryEntryCreate(BaseModel):
    student_id: str
    diary_date: str
    presence: Optional[str] = "Presente"
    teacher_attention: Optional[str] = None
    followed_agreements: Optional[str] = None
    activity_interest: Optional[str] = None
    had_lunch: Optional[str] = None
    participated_in_play: Optional[str] = None
    completed_activities: Optional[str] = None
    bathroom_use: Optional[str] = None
    open_observation: Optional[str] = None


class DiaryEntryUpdate(BaseModel):
    diary_date: Optional[str] = None
    presence: Optional[str] = None
    teacher_attention: Optional[str] = None
    followed_agreements: Optional[str] = None
    activity_interest: Optional[str] = None
    had_lunch: Optional[str] = None
    participated_in_play: Optional[str] = None
    completed_activities: Optional[str] = None
    bathroom_use: Optional[str] = None
    open_observation: Optional[str] = None


@router.get("/students")
@inject
async def list_students_with_diary(
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    return await repo.list_students_with_diary()


@router.get("/student/{student_id}")
@inject
async def list_entries(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    return await repo.list_by_student(student_id)


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_entry(
    body: DiaryEntryCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    data = body.model_dump()
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
