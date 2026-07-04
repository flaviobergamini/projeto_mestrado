from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Any
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.case_study_repository import CaseStudyRepository

router = APIRouter(prefix="/case-studies", tags=["Case Studies"])


class CaseStudyCreate(BaseModel):
    student_id: Optional[str] = None
    answers: dict[str, Any] = {}


class CaseStudyUpdate(BaseModel):
    student_id: Optional[str] = None
    answers: Optional[dict[str, Any]] = None


@router.get("")
@inject
async def list_case_studies(
    current_user: dict = Depends(get_current_user),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    return await repo.list_all()


@router.get("/{case_id}")
@inject
async def get_case_study(
    case_id: str,
    current_user: dict = Depends(get_current_user),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    case = await repo.get_by_id(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudo de caso não encontrado")
    return case


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_case_study(
    body: CaseStudyCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    data = body.model_dump()
    data["submitted_by"] = current_user.get("full_name") or current_user.get("username", "")
    return await repo.create(data)


@router.put("/{case_id}")
@inject
async def update_case_study(
    case_id: str,
    body: CaseStudyUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    updated = await repo.update(case_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudo de caso não encontrado")
    return updated


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_case_study(
    case_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    deleted = await repo.delete(case_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudo de caso não encontrado")
