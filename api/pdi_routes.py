from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.pdi_repository import PdiRepository

router = APIRouter(prefix="/pdi", tags=["PDI"])


class PdiCreate(BaseModel):
    student_id: str
    class_name: Optional[str] = None
    diagnosis: Optional[str] = None


class PdiUpdate(BaseModel):
    class_name: Optional[str] = None
    diagnosis: Optional[str] = None


class SubjectEntry(BaseModel):
    trimester: int
    subject: str
    skills: Optional[str] = None
    adaptations: Optional[str] = None
    learnings: Optional[str] = None


class SubjectsUpsert(BaseModel):
    subjects: list[SubjectEntry]


@router.get("")
@inject
async def list_pdis(
    current_user: dict = Depends(get_current_user),
    repo: PdiRepository = Depends(Provide[Container.pdi_repository]),
):
    return await repo.list_all()


@router.get("/{pdi_id}")
@inject
async def get_pdi(
    pdi_id: str,
    current_user: dict = Depends(get_current_user),
    repo: PdiRepository = Depends(Provide[Container.pdi_repository]),
):
    pdi = await repo.get_by_id(pdi_id)
    if not pdi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDI não encontrado")
    return pdi


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_pdi(
    body: PdiCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: PdiRepository = Depends(Provide[Container.pdi_repository]),
):
    data = body.model_dump()
    data["teacher_name"] = current_user.get("full_name") or current_user.get("username", "")
    return await repo.create(data)


@router.put("/{pdi_id}")
@inject
async def update_pdi(
    pdi_id: str,
    body: PdiUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: PdiRepository = Depends(Provide[Container.pdi_repository]),
):
    updated = await repo.update(pdi_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDI não encontrado")
    return updated


@router.delete("/{pdi_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_pdi(
    pdi_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: PdiRepository = Depends(Provide[Container.pdi_repository]),
):
    deleted = await repo.delete(pdi_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDI não encontrado")


@router.put("/{pdi_id}/subjects", status_code=status.HTTP_200_OK)
@inject
async def upsert_subjects(
    pdi_id: str,
    body: SubjectsUpsert,
    current_user: dict = Depends(get_current_user_read_write),
    repo: PdiRepository = Depends(Provide[Container.pdi_repository]),
):
    pdi = await repo.get_by_id(pdi_id)
    if not pdi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDI não encontrado")
    subjects = [s.model_dump() for s in body.subjects]
    return await repo.upsert_subjects(pdi_id, subjects)
