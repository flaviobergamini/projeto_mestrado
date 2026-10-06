"""Plano por habilidade com IA (rodadas 1 e 2). Camada HTTP apenas: a regra fica nos use cases."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.skill_plan.generate_skill_plan_draft_use_case import GenerateSkillPlanDraftUseCase
from core.use_case.skill_plan.suggest_skill_scores_use_case import SuggestSkillScoresUseCase
from core.use_case.skill_plan.list_skill_suggestions_use_case import ListSkillSuggestionsUseCase
from core.use_case.skill_plan.decide_skill_suggestion_use_case import DecideSkillSuggestionUseCase

router = APIRouter(prefix="/skill-plan", tags=["Skill Plan"])

READERS = ("admin", "secretaria", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "coordenacao", "professor")


class StudentBody(BaseModel):
    student_id: str


class DecideBody(BaseModel):
    accept: bool


def _unwrap(result: Result):
    if result.is_ok:
        return result.value
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.not_found_error)
    if result.is_bad_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.bad_request_error)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.error)


@router.post("/round1")
@inject
async def round1(
    body: StudentBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: GenerateSkillPlanDraftUseCase = Depends(Provide[Container.generate_skill_plan_draft_use_case]),
):
    """Rodada 1: rascunha o quadro das habilidades do PDI (só campos vazios; respeita 'sem IA')."""
    return _unwrap(await use_case.execute(body.student_id, current_user))


@router.post("/round2")
@inject
async def round2(
    body: StudentBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: SuggestSkillScoresUseCase = Depends(Provide[Container.suggest_skill_scores_use_case]),
):
    """Rodada 2: sugere mudanças de nota a partir do Kanban (a professora aceita ou recusa)."""
    return _unwrap(await use_case.execute(body.student_id, current_user))


@router.get("/suggestions")
@inject
async def list_suggestions(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: ListSkillSuggestionsUseCase = Depends(Provide[Container.list_skill_suggestions_use_case]),
):
    return _unwrap(await use_case.execute(student_id))


@router.post("/suggestions/{suggestion_id}/decide")
@inject
async def decide_suggestion(
    suggestion_id: str,
    body: DecideBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: DecideSkillSuggestionUseCase = Depends(Provide[Container.decide_skill_suggestion_use_case]),
):
    return _unwrap(await use_case.execute(suggestion_id, body.accept, current_user))
