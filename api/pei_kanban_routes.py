"""Quadro Kanban de execução do PEI. Camada HTTP apenas: a regra fica nos use cases."""
import asyncio
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.kanban import kanban_use_cases as uc
from core.services.skill_actions import actor_from_user, card_responsible, owns
from infrastructure.services.storage_service import StorageService
from infrastructure.utils.image_compression import compress_image, InvalidImageError

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
    summary: Optional[str] = None
    position: Optional[int] = None


class FromSkillBody(BaseModel):
    student_id: str
    skill_id: str
    only_existing: bool = False  # true: só atualiza cards já ligados (usado ao salvar o plano)


def _unwrap(result: Result):
    if result.is_ok:
        return result.value
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.not_found_error)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.bad_request_error or result.error)


async def _own_card_or_404(repo, card_id: str, user: dict) -> dict:
    """Card de outro professor não existe para este usuário (a coordenação vê todos)."""
    card = await repo.get(card_id)
    if not card or not owns(card_responsible(card), actor_from_user(user)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card não encontrado")
    return card


def _author(user: dict) -> str:
    return user.get("full_name") or user.get("username", "")


async def _sign_photos(cards: list[dict]) -> None:
    """Troca as chaves do storage por [{key, url}] com URL assinada (uma chamada só para o quadro todo)."""
    keys = [k for c in cards for k in c.get("photos") or []]
    signed = await StorageService().create_signed_urls_batch_async(keys) if keys else {}
    for c in cards:
        c["photos"] = [{"key": k, "url": signed.get(k, "")} for k in c.get("photos") or []]


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


@router.get("")
@inject
async def list_kanban_cards(
    student_id: str = Query(...),
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.ListKanbanCardsUseCase = Depends(Provide[Container.list_kanban_cards_use_case]),
):
    cards = _unwrap(await use_case.execute(student_id, current_user))
    await _sign_photos(cards)
    return cards


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_kanban_card(
    body: KanbanCardCreate,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.CreateKanbanCardUseCase = Depends(Provide[Container.create_kanban_card_use_case]),
):
    return _unwrap(await use_case.execute(body.model_dump(), _author(current_user), current_user))


@router.post("/from-skill", status_code=status.HTTP_201_CREATED)
@inject
async def create_cards_from_skill(
    body: FromSkillBody,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.CreateCardsFromSkillUseCase = Depends(Provide[Container.create_cards_from_skill_use_case]),
):
    """Envia as ações práticas do plano de uma habilidade para o Kanban."""
    return _unwrap(await use_case.execute(body.student_id, body.skill_id, _author(current_user), body.only_existing))


@router.patch("/{card_id}")
@inject
async def update_kanban_card(
    card_id: str,
    body: KanbanCardUpdate,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.UpdateKanbanCardUseCase = Depends(Provide[Container.update_kanban_card_use_case]),
):
    card = _unwrap(await use_case.execute(card_id, body.model_dump(exclude_none=True), current_user))
    await _sign_photos([card])
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_kanban_card(
    card_id: str,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.DeleteKanbanCardUseCase = Depends(Provide[Container.delete_kanban_card_use_case]),
):
    _unwrap(await use_case.execute(card_id, current_user))


@router.post("/{card_id}/summary")
@inject
async def generate_card_summary(
    card_id: str,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    use_case: uc.GenerateKanbanCardSummaryUseCase = Depends(Provide[Container.generate_kanban_card_summary_use_case]),
):
    """A IA resume o diário da ação e grava o resumo no card."""
    card = _unwrap(await use_case.execute(card_id, current_user))
    await _sign_photos([card])
    return card


@router.post("/{card_id}/photos", status_code=status.HTTP_201_CREATED)
@inject
async def add_card_photo(
    card_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo=Depends(Provide[Container.pei_kanban_repository]),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="Tipo de arquivo não permitido. Use JPEG, PNG, GIF ou WebP.")
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Imagem muito grande. Máximo permitido: 10 MB.")
    try:
        compressed = await asyncio.to_thread(compress_image, content)
    except InvalidImageError:
        raise HTTPException(status_code=422, detail="Arquivo de imagem inválido ou corrompido.")
    await _own_card_or_404(repo, card_id, current_user)
    key = f"kanban/{card_id}/{uuid.uuid4()}.jpg"
    await asyncio.to_thread(StorageService().upload, key, compressed.content, compressed.mime_type)
    card = await repo.add_photo(card_id, key)
    await _sign_photos([card])
    return card


@router.delete("/{card_id}/photos")
@inject
async def remove_card_photo(
    card_id: str,
    key: str = Query(...),
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo=Depends(Provide[Container.pei_kanban_repository]),
):
    if not key.startswith(f"kanban/{card_id}/"):
        raise HTTPException(status_code=422, detail="Foto inválida para este card.")
    await _own_card_or_404(repo, card_id, current_user)
    card = await repo.remove_photo(card_id, key)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado")
    await asyncio.to_thread(StorageService().delete, key)
    await _sign_photos([card])
    return card
