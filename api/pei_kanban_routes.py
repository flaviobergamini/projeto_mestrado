"""Quadro Kanban de execução do PEI — um card por seção do PEI gerado (automático)
ou criado manualmente pelo professor, movido entre 'A fazer' / 'Fazendo' / 'Concluído'."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from infrastructure.repositories.pei_kanban_repository import PeiKanbanRepository, VALID_STATUSES

router = APIRouter(prefix="/pei-kanban", tags=["PEI Kanban"])

VIEW_ROLES = ("admin", "coordenacao", "professor")


class KanbanCardCreate(BaseModel):
    student_id: str
    title: str
    description: Optional[str] = None
    status: str = "todo"

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status deve ser um de: {VALID_STATUSES}")
        return v


class KanbanCardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    reaction: Optional[int] = None
    position: Optional[int] = None

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status deve ser um de: {VALID_STATUSES}")
        return v

    @field_validator("reaction")
    @classmethod
    def _validate_reaction(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("reaction deve estar entre 1 e 5")
        return v


@router.get("")
@inject
async def list_kanban_cards(
    student_id: str = Query(...),
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: PeiKanbanRepository = Depends(Provide[Container.pei_kanban_repository]),
):
    return await repo.list_by_student(student_id)


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_kanban_card(
    body: KanbanCardCreate,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: PeiKanbanRepository = Depends(Provide[Container.pei_kanban_repository]),
):
    data = body.model_dump()
    data["created_by"] = current_user.get("full_name") or current_user.get("username", "")
    data["source"] = "manual"
    return await repo.create(data)


@router.patch("/{card_id}")
@inject
async def update_kanban_card(
    card_id: str,
    body: KanbanCardUpdate,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: PeiKanbanRepository = Depends(Provide[Container.pei_kanban_repository]),
):
    updated = await repo.update(card_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card não encontrado")
    return updated


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_kanban_card(
    card_id: str,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: PeiKanbanRepository = Depends(Provide[Container.pei_kanban_repository]),
):
    deleted = await repo.delete(card_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card não encontrado")
