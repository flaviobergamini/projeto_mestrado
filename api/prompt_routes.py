from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user
from core.kernel.container import Container
from infrastructure.repositories.prompt_repository import PromptRepository

router = APIRouter(prefix="/prompts", tags=["Prompts"])

VALID_SCOPES = {"chat", "pei"}
EDITOR_ROLES = {"admin", "coordenacao"}


class PromptCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    content: str


class PromptUpdate(BaseModel):
    name: str
    description: Optional[str] = ""
    content: str


def _require_editor(current_user: dict):
    if current_user.get("role", "") not in EDITOR_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Apenas admin ou coordenação podem gerenciar prompts.")


def _check_scope(scope: str):
    if scope not in VALID_SCOPES:
        raise HTTPException(status_code=400, detail=f"Escopo inválido. Use: {sorted(VALID_SCOPES)}")


@router.get("/{scope}/active")
@inject
async def get_active_prompt(
    scope: str,
    current_user: dict = Depends(get_current_user),
    repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    _check_scope(scope)
    return await repo.get_active(scope)


@router.get("/{scope}")
@inject
async def list_prompts(
    scope: str,
    current_user: dict = Depends(get_current_user),
    repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    _check_scope(scope)
    return await repo.list_all(scope)


@router.post("/{scope}", status_code=201)
@inject
async def create_prompt(
    scope: str,
    body: PromptCreate,
    current_user: dict = Depends(get_current_user),
    repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    _check_scope(scope)
    _require_editor(current_user)
    return await repo.create(scope, body.name, body.description or "", body.content)


@router.put("/{scope}/{prompt_id}")
@inject
async def update_prompt(
    scope: str,
    prompt_id: str,
    body: PromptUpdate,
    current_user: dict = Depends(get_current_user),
    repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    _check_scope(scope)
    _require_editor(current_user)
    updated = await repo.update(prompt_id, body.name, body.description or "", body.content)
    if not updated:
        raise HTTPException(status_code=404, detail="Prompt não encontrado.")
    return updated


@router.post("/{scope}/{prompt_id}/activate")
@inject
async def activate_prompt(
    scope: str,
    prompt_id: str,
    current_user: dict = Depends(get_current_user),
    repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    _check_scope(scope)
    _require_editor(current_user)
    result = await repo.activate(scope, prompt_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt não encontrado.")
    return result


@router.delete("/{scope}/{prompt_id}", status_code=204)
@inject
async def delete_prompt(
    scope: str,
    prompt_id: str,
    current_user: dict = Depends(get_current_user),
    repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    _check_scope(scope)
    _require_editor(current_user)
    deleted = await repo.delete(prompt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prompt não encontrado.")


@router.post("/{scope}/reset")
@inject
async def reset_prompt(
    scope: str,
    current_user: dict = Depends(get_current_user),
    repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    _check_scope(scope)
    _require_editor(current_user)
    return await repo.reset_to_default(scope)
