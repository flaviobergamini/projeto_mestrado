"""Quadro Kanban de execução do PEI. Camada HTTP apenas: a regra fica nos use cases."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.kanban import kanban_use_cases as uc

router = APIRouter(prefix="/pei-kanban", tags=["PEI Kanban"])

VIEW_ROLES = ("admin", "coordenacao", "professor")


class KanbanCardCreate(BaseModel):
    student_id: str
    title: str
    description: Optional[str] = None
    status: str = "todo"


class KanbanCardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    reaction: Optional[int] = None
    adaptation: Optional[str] = None
    daily_log: Optional[str] = None
    position: Optional[int] = None


class FromSkillBody(BaseModel):
    student_id: str
    skill_id: str


def _unwrap(result: Result):
    if result.is_ok:
        return result.value
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.not_found_error)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.bad_request_error or result.error)


def _author(user: dict) -> str:
    return user.get("full_name") or user.get("username", "")


@router.get("")
@inject
async def list_kanban_cards(
    student_id: str = Query(...),
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.ListKanbanCardsUseCase = Depends(Provide[Container.list_kanban_cards_use_case]),
):
    return _unwrap(await use_case.execute(student_id))


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_kanban_card(
    body: KanbanCardCreate,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.CreateKanbanCardUseCase = Depends(Provide[Container.create_kanban_card_use_case]),
):
    return _unwrap(await use_case.execute(body.model_dump(), _author(current_user)))


@router.post("/from-skill", status_code=status.HTTP_201_CREATED)
@inject
async def create_cards_from_skill(
    body: FromSkillBody,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.CreateCardsFromSkillUseCase = Depends(Provide[Container.create_cards_from_skill_use_case]),
):
    """Envia as ações práticas do plano de uma habilidade para o Kanban."""
    return _unwrap(await use_case.execute(body.student_id, body.skill_id, _author(current_user)))


@router.patch("/{card_id}")
@inject
async def update_kanban_card(
    card_id: str,
    body: KanbanCardUpdate,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.UpdateKanbanCardUseCase = Depends(Provide[Container.update_kanban_card_use_case]),
):
    return _unwrap(await use_case.execute(card_id, body.model_dump(exclude_none=True)))


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_kanban_card(
    card_id: str,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.DeleteKanbanCardUseCase = Depends(Provide[Container.delete_kanban_card_use_case]),
):
    _unwrap(await use_case.execute(card_id))
