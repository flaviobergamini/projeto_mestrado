"""Relações entre habilidades (mapa do submenu Relações do PDI). Camada HTTP apenas: a regra fica nos use cases."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from api.student_access import guard_student_scope
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.skill_relations.skill_relation_use_cases import (
    SkillRelationUseCases, GenerateSkillRelationsUseCase, GenerateRelationAdaptationsUseCase,
)

router = APIRouter(prefix="/skill-relations", tags=["Skill Relations"], dependencies=[Depends(guard_student_scope)])

READERS = ("admin", "secretaria", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "coordenacao", "professor")


class RelationBody(BaseModel):
    related_skill_id: str
    direction: str = Field("both", pattern="^(in|out|both)$")  # both: sem seta; out: finalística -> habilidade; in: o inverso
    reason: str = Field("", max_length=2000)
    x: Optional[float] = None  # onde o card foi solto no mapa
    y: Optional[float] = None


class RelationPatch(BaseModel):
    adaptation: Optional[str] = Field(None, max_length=4000)
    actions: Optional[list[str]] = Field(None, max_length=10)
    direction: Optional[str] = Field(None, pattern="^(in|out|both)$")
    reason: Optional[str] = Field(None, max_length=2000)
    justification: Optional[str] = Field(None, max_length=2000)  # nome antigo de `reason`
    x: Optional[float] = Field(None, ge=0, le=2000)
    y: Optional[float] = Field(None, ge=0, le=2000)


class Position(BaseModel):
    x: float = Field(ge=0, le=2000)
    y: float = Field(ge=0, le=2000)


class LayoutBody(BaseModel):
    positions: dict[str, Optional[Position]] = Field(max_length=200)  # valor nulo: volta ao layout padrão


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
    """Habilidades do aluno com 1 a 4 estrelas (as que podem entrar no grafo), com a marca de finalística e o nº de relações."""
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


@router.get("/students/{student_id}/skills/{skill_id}/graph")
@inject
async def graph_json(
    student_id: str,
    skill_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    """O grafo em JSON como a IA o recebe (anonimizável: sem ids de relação, só códigos, estrelas, observações e setas)."""
    return _unwrap(await use_case.graph_json(student_id, skill_id))


@router.put("/students/{student_id}/skills/{skill_id}/layout")
@inject
async def save_layout(
    student_id: str,
    skill_id: str,
    body: LayoutBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    """Grava as posições dos nós no mapa (parte do JSON do grafo)."""
    return _unwrap(await use_case.set_layout(
        student_id, skill_id, {k: (v.model_dump() if v else None) for k, v in body.positions.items()}, current_user))


@router.delete("/students/{student_id}/skills/{skill_id}/relations")
@inject
async def clear_relations(
    student_id: str,
    skill_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    """Apaga todas as relações da finalística (as habilidades voltam para "sem relações")."""
    return _unwrap(await use_case.clear(student_id, skill_id, current_user))


@router.get("/students/{student_id}/skills/{skill_id}/preview")
@inject
async def preview_ai_request(
    student_id: str,
    skill_id: str,
    action: str = "relations",
    current_user: dict = Depends(require_roles(*WRITERS)),
    relations: GenerateSkillRelationsUseCase = Depends(Provide[Container.generate_skill_relations_use_case]),
    adaptations: GenerateRelationAdaptationsUseCase = Depends(Provide[Container.generate_relation_adaptations_use_case]),
):
    """O que seria enviado à IA (anonimizado) ao gerar relações ou adaptações. Não chama a IA."""
    use_case = adaptations if action == "adaptations" else relations
    return _unwrap(await use_case.preview(student_id, skill_id))


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


@router.post("/students/{student_id}/skills/{skill_id}/adaptations")
@inject
async def generate_adaptations(
    student_id: str,
    skill_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: GenerateRelationAdaptationsUseCase = Depends(Provide[Container.generate_relation_adaptations_use_case]),
):
    """IA escreve a adaptação e as ações de cada nó do grafo (grava no JSON; não sobrescreve edições manuais)."""
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
    return _unwrap(await use_case.update(student_id, relation_id, body.model_dump(exclude_unset=True), current_user))


@router.delete("/students/{student_id}/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_relation(
    student_id: str,
    relation_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: SkillRelationUseCases = Depends(Provide[Container.skill_relation_use_cases]),
):
    _unwrap(await use_case.delete(student_id, relation_id, current_user))
