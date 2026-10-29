"""Plano por habilidade com IA (geração de adaptações e resumo). Camada HTTP apenas: a regra fica nos use cases."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.use_case.skill_plan.prompts import SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_LIMITS, LIMIT_RANGE
from infrastructure.repositories.app_settings_repository import AppSettingsRepository
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.skill_plan.generate_skill_plan_draft_use_case import GenerateSkillPlanDraftUseCase
from core.use_case.skill_plan.generate_skill_summary_use_case import GenerateSkillSummaryUseCase

router = APIRouter(prefix="/skill-plan", tags=["Skill Plan"])

READERS = ("admin", "secretaria", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "coordenacao", "professor")


class StudentBody(BaseModel):
    student_id: str


class SkillSummaryBody(BaseModel):
    student_id: str
    skill_id: str



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


PROMPT_MANAGERS = ("admin", "coordenacao")


class LimitsBody(BaseModel):
    max_adaptations: int
    max_actions: int


@router.get("/round1/settings")
@inject
async def round1_settings(
    current_user: dict = Depends(require_roles(*PROMPT_MANAGERS)),
    repo: AppSettingsRepository = Depends(Provide[Container.app_settings_repository]),
):
    """Limites máximos de adaptações por habilidade e de ações por adaptação na geração da rodada 1."""
    return await repo.get(SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_LIMITS)


@router.put("/round1/settings")
@inject
async def save_round1_settings(
    body: LimitsBody,
    current_user: dict = Depends(require_roles(*PROMPT_MANAGERS)),
    repo: AppSettingsRepository = Depends(Provide[Container.app_settings_repository]),
):
    lo, hi = LIMIT_RANGE
    if not (lo <= body.max_adaptations <= hi and lo <= body.max_actions <= hi):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Use valores de {lo} a {hi}.")
    return await repo.set(SKILL_PLAN_SETTINGS_KEY, {"max_adaptations": body.max_adaptations, "max_actions": body.max_actions})


@router.get("/round1/preview")
@inject
async def round1_preview(
    student_id: str,
    current_user: dict = Depends(require_roles(*PROMPT_MANAGERS)),
    use_case: GenerateSkillPlanDraftUseCase = Depends(Provide[Container.generate_skill_plan_draft_use_case]),
):
    """Prévia do que é enviado à IA para um aluno (prompt do sistema + contexto anonimizado + habilidades). Não chama a IA."""
    return _unwrap(await use_case.preview(student_id))


@router.post("/summary")
@inject
async def generate_summary(
    body: SkillSummaryBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: GenerateSkillSummaryUseCase = Depends(Provide[Container.generate_skill_summary_use_case]),
):
    """Gera o resumo da habilidade com IA (não salva: a professora revisa e grava com o plano)."""
    return _unwrap(await use_case.execute(body.student_id, body.skill_id, current_user))
