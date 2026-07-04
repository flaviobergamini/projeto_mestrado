from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.teacher_repository import TeacherRepository

router = APIRouter(prefix="/teachers", tags=["Teachers"])


class TeacherCreate(BaseModel):
    name: str
    school_id: Optional[str] = None
    specialization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    school_id: Optional[str] = None
    specialization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
@inject
async def list_teachers(
    current_user: dict = Depends(get_current_user),
    repo: TeacherRepository = Depends(Provide[Container.teacher_repository]),
):
    return await repo.list_all()


@router.get("/{teacher_id}")
@inject
async def get_teacher(
    teacher_id: str,
    current_user: dict = Depends(get_current_user),
    repo: TeacherRepository = Depends(Provide[Container.teacher_repository]),
):
    teacher = await repo.get_by_id(teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")
    return teacher


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_teacher(
    body: TeacherCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: TeacherRepository = Depends(Provide[Container.teacher_repository]),
):
    return await repo.create(body.model_dump())


@router.put("/{teacher_id}")
@inject
async def update_teacher(
    teacher_id: str,
    body: TeacherUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: TeacherRepository = Depends(Provide[Container.teacher_repository]),
):
    updated = await repo.update(teacher_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")
    return updated


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_teacher(
    teacher_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: TeacherRepository = Depends(Provide[Container.teacher_repository]),
):
    deleted = await repo.delete(teacher_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")
