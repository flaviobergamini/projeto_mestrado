"""Skills — prompts pré-definidos que o admin cadastra e professores/coordenação
usam no chat pra tarefas recorrentes (relatórios, resumos, etc.).

"Rodar" uma skill não tem lógica própria: o frontend apenas envia `skill.prompt`
como mensagem para o endpoint de chat já existente (POST /chat/message) — mesmo
comportamento da PoC, que reaproveita a rota de chat comum em vez de ter um
endpoint de execução dedicado.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from infrastructure.repositories.skill_repository import SkillRepository

router = APIRouter(prefix="/skills", tags=["Skills"])

# Mesmos roles que têm acesso à página de Chat no frontend
VIEW_ROLES = ("admin", "coordenacao", "professor")


class SkillCreate(BaseModel):
    title: str
    prompt: str
    description: Optional[str] = None


class SkillUpdate(BaseModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    description: Optional[str] = None


@router.get("")
@inject
async def list_skills(
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: SkillRepository = Depends(Provide[Container.skill_repository]),
):
    return await repo.list_all()


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_skill(
    body: SkillCreate,
    current_user: dict = Depends(require_roles("admin")),
    repo: SkillRepository = Depends(Provide[Container.skill_repository]),
):
    data = body.model_dump()
    data["created_by"] = current_user.get("full_name") or current_user.get("username", "")
    return await repo.create(data)


@router.put("/{skill_id}")
@inject
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    current_user: dict = Depends(require_roles("admin")),
    repo: SkillRepository = Depends(Provide[Container.skill_repository]),
):
    updated = await repo.update(skill_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill não encontrada")
    return updated


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_skill(
    skill_id: str,
    current_user: dict = Depends(require_roles("admin")),
    repo: SkillRepository = Depends(Provide[Container.skill_repository]),
):
    deleted = await repo.delete(skill_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill não encontrada")
