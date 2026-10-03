from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from infrastructure.repositories.bncc_repository import BnccRepository, BnccError
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.services.skill_report_pdf import generate_skill_report_pdf

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


# ── catálogo ──────────────────────────────────────────────────────────────────

@router.get("/grades")
@inject
async def list_grades(
    current_user: dict = Depends(require_roles(*READERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    return await repo.list_grades()


@router.get("/areas")
@inject
async def list_areas(
    current_user: dict = Depends(require_roles(*READERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    return await repo.list_areas()


@router.get("/skills")
@inject
async def list_skills(
    grades: Optional[str] = Query(None, description="anos separados por |"),
    areas: Optional[str] = Query(None, description="áreas separadas por |"),
    q: Optional[str] = None,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    return await repo.list_skills(_csv(grades), _csv(areas), q)


@router.post("/skills", status_code=status.HTTP_201_CREATED)
@inject
async def create_skill(
    body: SkillBody,
    current_user: dict = Depends(require_roles(*CATALOG_EDITORS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    try:
        return await repo.create_skill(body.model_dump())
    except BnccError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/skills/{skill_id}")
@inject
async def update_skill(
    skill_id: str,
    body: SkillBody,
    current_user: dict = Depends(require_roles(*CATALOG_EDITORS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    try:
        updated = await repo.update_skill(skill_id, body.model_dump())
    except BnccError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habilidade não encontrada")
    return updated


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_skill(
    skill_id: str,
    current_user: dict = Depends(require_roles(*CATALOG_EDITORS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    if not await repo.delete_skill(skill_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habilidade não encontrada")


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
    current_user: dict = Depends(require_roles(*READERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    return await repo.student_skills(
        student_id, _csv(grades), _csv(areas), q, min_score, max_score, only_with_observation,
    )


@router.put("/students/{student_id}/skills/{skill_id}")
@inject
async def set_score(
    student_id: str,
    skill_id: str,
    body: ScoreBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    try:
        return await repo.set_score(
            student_id, skill_id, {k: getattr(body, k) for k in body.model_fields_set}, current_user,
        )
    except BnccError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── relatórios ────────────────────────────────────────────────────────────────

@router.post("/students/{student_id}/reports", status_code=status.HTTP_201_CREATED)
@inject
async def create_report(
    student_id: str,
    body: ReportBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    try:
        return await repo.create_report(student_id, body.model_dump(), current_user)
    except BnccError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/students/{student_id}/reports")
@inject
async def list_reports(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    return await repo.list_reports(student_id)


@router.get("/reports/{report_id}")
@inject
async def get_report(
    report_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    report = await repo.get_report(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")
    return report


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_report(
    report_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    if not await repo.delete_report(report_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")


@router.get("/reports/{report_id}/pdf")
@inject
async def report_pdf(
    report_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    report = await repo.get_report(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")
    student = await student_repo.get_by_id(report["student_id"])
    pdf = generate_skill_report_pdf(report, (student or {}).get("name") or "Aluno")
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="habilidades_bncc_{report_id[:8]}.pdf"'},
    )
