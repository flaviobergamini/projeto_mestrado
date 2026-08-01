from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.school_repository import SchoolRepository

router = APIRouter(prefix="/schools", tags=["Schools"])


class SchoolCreate(BaseModel):
    name: str
    cnpj: Optional[str] = None
    institution_type: Optional[str] = None
    address_city: Optional[str] = None
    notes: Optional[str] = None


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None
    institution_type: Optional[str] = None
    address_city: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
@inject
async def list_schools(
    current_user: dict = Depends(get_current_user),
    repo: SchoolRepository = Depends(Provide[Container.school_repository]),
):
    return await repo.list_all()


@router.get("/{school_id}")
@inject
async def get_school(
    school_id: str,
    current_user: dict = Depends(get_current_user),
    repo: SchoolRepository = Depends(Provide[Container.school_repository]),
):
    school = await repo.get_by_id(school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escola não encontrada")
    return school


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_school(
    body: SchoolCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: SchoolRepository = Depends(Provide[Container.school_repository]),
):
    return await repo.create(body.model_dump())


@router.put("/{school_id}")
@inject
async def update_school(
    school_id: str,
    body: SchoolUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: SchoolRepository = Depends(Provide[Container.school_repository]),
):
    updated = await repo.update(school_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escola não encontrada")
    return updated


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_school(
    school_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: SchoolRepository = Depends(Provide[Container.school_repository]),
):
    deleted = await repo.delete(school_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escola não encontrada")
