from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.bncc import bncc_use_cases as uc

router = APIRouter(prefix="/bncc", tags=["BNCC"])

# Equipe pedagógica: lê (inclui viewer) e escreve notas/relatórios.
READERS = ("admin", "secretaria", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "secretaria", "coordenacao", "professor")
# Quem edita o catálogo de códigos e descrições.
CATALOG_EDITORS = ("admin", "secretaria", "coordenacao")


class SkillBody(BaseModel):
    stage: str = "fundamental"
    grade: str = Field(max_length=80)
    area: str = Field(max_length=160)
    code: str = Field(max_length=40)
    description: str


class ScoreBody(BaseModel):
    score: Optional[int] = Field(None, ge=0, le=5)
    observation: Optional[str] = Field(None, max_length=2000)
    adaptation: Optional[str] = Field(None, max_length=4000)
    justification: Optional[str] = Field(None, max_length=4000)
    actions: Optional[str] = Field(None, max_length=4000)
    correlated_codes: Optional[list[str]] = None
    ai_excluded: Optional[bool] = None
    in_plan: Optional[bool] = None
    change_note: Optional[str] = Field(None, max_length=2000)
    evidence_card_ids: Optional[list[str]] = None


class ReportBody(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    grades: list[str] = []
    areas: list[str] = []
    min_score: Optional[int] = Field(None, ge=0, le=5)
    max_score: Optional[int] = Field(None, ge=0, le=5)
    include_observations: bool = True
    only_with_observation: bool = False
    query: Optional[str] = None


def _csv(value: Optional[str]) -> Optional[list[str]]:
    items = [v.strip() for v in (value or "").split("|") if v.strip()]
    return items or None


def _unwrap(result: Result):
    """Traduz o Result do use case em resposta HTTP."""
    if result.is_ok:
        return result.value
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.not_found_error)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.bad_request_error or result.error)


# ── catálogo ──────────────────────────────────────────────────────────────────

@router.get("/grades")
@inject
async def list_grades(
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListGradesUseCase = Depends(Provide[Container.bncc_list_grades_use_case]),
):
    return _unwrap(await use_case.execute())


@router.get("/areas")
@inject
async def list_areas(
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListAreasUseCase = Depends(Provide[Container.bncc_list_areas_use_case]),
):
    return _unwrap(await use_case.execute())


@router.get("/skills")
@inject
async def list_skills(
    grades: Optional[str] = Query(None, description="anos separados por |"),
    areas: Optional[str] = Query(None, description="áreas separadas por |"),
    q: Optional[str] = None,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListSkillsUseCase = Depends(Provide[Container.bncc_list_skills_use_case]),
):
    return _unwrap(await use_case.execute(_csv(grades), _csv(areas), q))


@router.post("/skills", status_code=status.HTTP_201_CREATED)
@inject
async def create_skill(
    body: SkillBody,
    current_user: dict = Depends(require_roles(*CATALOG_EDITORS)),
    use_case: uc.CreateSkillUseCase = Depends(Provide[Container.bncc_create_skill_use_case]),
):
    return _unwrap(await use_case.execute(body.model_dump()))


@router.put("/skills/{skill_id}")
@inject
async def update_skill(
    skill_id: str,
    body: SkillBody,
    current_user: dict = Depends(require_roles(*CATALOG_EDITORS)),
    use_case: uc.UpdateSkillUseCase = Depends(Provide[Container.bncc_update_skill_use_case]),
):
    return _unwrap(await use_case.execute(skill_id, body.model_dump()))


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_skill(
    skill_id: str,
    current_user: dict = Depends(require_roles(*CATALOG_EDITORS)),
    use_case: uc.DeleteSkillUseCase = Depends(Provide[Container.bncc_delete_skill_use_case]),
):
    _unwrap(await use_case.execute(skill_id))


# ── notas por aluno ───────────────────────────────────────────────────────────

@router.get("/students/{student_id}/skills")
@inject
async def student_skills(
    student_id: str,
    grades: Optional[str] = Query(None, description="anos separados por |"),
    areas: Optional[str] = Query(None, description="áreas separadas por |"),
    q: Optional[str] = None,
    min_score: Optional[int] = Query(None, ge=0, le=5),
    max_score: Optional[int] = Query(None, ge=0, le=5),
    only_with_observation: bool = False,
    only_in_plan: bool = False,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListStudentSkillsUseCase = Depends(Provide[Container.bncc_list_student_skills_use_case]),
):
    return _unwrap(await use_case.execute(
        student_id, grades=_csv(grades), areas=_csv(areas), q=q, min_score=min_score, max_score=max_score,
        only_with_observation=only_with_observation, only_in_plan=only_in_plan,
    ))


@router.get("/students/{student_id}/skills/{skill_id}/events")
@inject
async def skill_events(
    student_id: str,
    skill_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListSkillEventsUseCase = Depends(Provide[Container.bncc_list_skill_events_use_case]),
):
    return _unwrap(await use_case.execute(student_id, skill_id))


@router.put("/students/{student_id}/skills/{skill_id}")
@inject
async def set_score(
    student_id: str,
    skill_id: str,
    body: ScoreBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: uc.SetSkillScoreUseCase = Depends(Provide[Container.bncc_set_skill_score_use_case]),
):
    return _unwrap(await use_case.execute(
        student_id, skill_id, {k: getattr(body, k) for k in body.model_fields_set}, current_user,
    ))


# ── relatórios ────────────────────────────────────────────────────────────────

@router.post("/students/{student_id}/reports", status_code=status.HTTP_201_CREATED)
@inject
async def create_report(
    student_id: str,
    body: ReportBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: uc.CreateSkillReportUseCase = Depends(Provide[Container.bncc_create_report_use_case]),
):
    return _unwrap(await use_case.execute(student_id, body.model_dump(), current_user))


@router.get("/students/{student_id}/reports")
@inject
async def list_reports(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListSkillReportsUseCase = Depends(Provide[Container.bncc_list_reports_use_case]),
):
    return _unwrap(await use_case.execute(student_id))


@router.get("/reports/{report_id}")
@inject
async def get_report(
    report_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.GetSkillReportUseCase = Depends(Provide[Container.bncc_get_report_use_case]),
):
    return _unwrap(await use_case.execute(report_id))


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_report(
    report_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: uc.DeleteSkillReportUseCase = Depends(Provide[Container.bncc_delete_report_use_case]),
):
    _unwrap(await use_case.execute(report_id))


@router.get("/reports/{report_id}/pdf")
@inject
async def report_pdf(
    report_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.RenderSkillReportPdfUseCase = Depends(Provide[Container.bncc_report_pdf_use_case]),
):
    pdf = _unwrap(await use_case.execute(report_id))
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="habilidades_bncc_{report_id[:8]}.pdf"'},
    )
