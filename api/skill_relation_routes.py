"""Relações entre habilidades (mapa do submenu Relações do PDI). Camada HTTP apenas: a regra fica nos use cases."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from api.student_access import guard_student_scope
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.skill_relations.skill_relation_use_cases import SkillRelationUseCases, GenerateSkillRelationsUseCase

router = APIRouter(prefix="/skill-relations", tags=["Skill Relations"], dependencies=[Depends(guard_student_scope)])

READERS = ("admin", "secretaria", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "coordenacao", "professor")


class RelationBody(BaseModel):
    kind: str = Field(pattern="^(skill|field)$")
    related_skill_id: Optional[str] = None
    field_key: Optional[str] = None
    adaptation: str = Field("", max_length=4000)
    justification: str = Field("", max_length=4000)
    actions: list[str] = Field(default_factory=list, max_length=20)


class RelationPatch(BaseModel):
    adaptation: Optional[str] = Field(None, max_length=4000)
    justification: Optional[str] = Field(None, max_length=4000)
    actions: Optional[list[str]] = Field(None, max_length=20)


def _unwrap(result: Result):
    if result.is_ok:
        return result.value
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.not_found_error)
    if result.is_bad_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.bad_request_error)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.error)


@router.get("/students/{student_id}")
@inject
async def overview(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    """Habilidades do aluno que têm relações ou estão marcadas como indiretas."""
    return _unwrap(await use_case.overview(student_id))


@router.get("/students/{student_id}/skills/{skill_id}")
@inject
async def list_relations(
    student_id: str,
    skill_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    return _unwrap(await use_case.list_relations(student_id, skill_id))


@router.post("/students/{student_id}/skills/{skill_id}", status_code=status.HTTP_201_CREATED)
@inject
async def create_relation(
    student_id: str,
    skill_id: str,
    body: RelationBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    return _unwrap(await use_case.create(student_id, skill_id, body.model_dump(), current_user))


@router.post("/students/{student_id}/skills/{skill_id}/generate")
@inject
async def generate_relations(
    student_id: str,
    skill_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: GenerateSkillRelationsUseCase = Depends(Provide[Container.generate_skill_relations_use_case]),
):
    """IA relaciona a habilidade com outras habilidades e campos de experiência (só acrescenta; custo no Gemini)."""
    return _unwrap(await use_case.execute(student_id, skill_id, current_user))


@router.put("/students/{student_id}/{relation_id}")
@inject
async def update_relation(
    student_id: str,
    relation_id: str,
    body: RelationPatch,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    return _unwrap(await use_case.update(student_id, relation_id, body.model_dump(exclude_unset=True)))


@router.delete("/students/{student_id}/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_relation(
    student_id: str,
    relation_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    _unwrap(await use_case.delete(student_id, relation_id))
