"""Métricas agregadas de frequência/adesão pro painel administrativo.

Todos os endpoints filtram e agregam via SQL (ver infrastructure/repositories/
metrics_repository.py) — nada é agregado em Python pra não pagar o custo de
carregar todas as linhas de diary_entries a cada carregamento do painel.

Restrito a admin/coordenação: são dados agregados, mas cruzam informações
sensíveis (nível de suporte, perfil socioeconômico dos responsáveis).
"""
from datetime import date as _date
from typing import Optional
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from infrastructure.repositories.metrics_repository import MetricsRepository

router = APIRouter(prefix="/admin/metrics", tags=["Admin Metrics"])


@router.get("/diary-fill-by-student-age")
@inject
async def diary_fill_by_student_age(
    date_from: Optional[_date] = None,
    date_to: Optional[_date] = None,
    source: str = "school",
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """Frequência de preenchimento do diário × faixa etária do aluno, segregada por escola/município."""
    return await repo.diary_fill_by_student_age(date_from, date_to, source)


@router.get("/diary-fill-by-support-level")
@inject
async def diary_fill_by_support_level(
    date_from: Optional[_date] = None,
    date_to: Optional[_date] = None,
    source: str = "school",
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """Frequência de preenchimento do diário × nível de suporte do autismo (1/2/3)."""
    return await repo.diary_fill_by_support_level(date_from, date_to, source)


@router.get("/absences-by-type")
@inject
async def absences_by_type(
    date_from: Optional[_date] = None,
    date_to: Optional[_date] = None,
    school_id: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """Faltas justificadas x injustificadas, por escola."""
    return await repo.absences_by_type(date_from, date_to, school_id)


@router.get("/students-per-teacher")
@inject
async def students_per_teacher(
    school_id: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """Índice de alunos por professor, por escola."""
    return await repo.students_per_teacher(school_id)


@router.get("/teacher-demographics")
@inject
async def teacher_demographics(
    school_id: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """Composição do corpo docente: gênero, faixa etária e especialidade (regente/apoio/AEE/etc.), por escola."""
    return await repo.teacher_demographics(school_id)


@router.get("/diary-fill-by-teacher-attributes")
@inject
async def diary_fill_by_teacher_attributes(
    date_from: Optional[_date] = None,
    date_to: Optional[_date] = None,
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """Frequência de preenchimento do diário × especialidade/gênero/idade do professor vinculado ao aluno."""
    return await repo.diary_fill_by_teacher_attributes(date_from, date_to)


@router.get("/diary-fill-by-parent-profile")
@inject
async def diary_fill_by_parent_profile(
    date_from: Optional[_date] = None,
    date_to: Optional[_date] = None,
    current_user: dict = Depends(require_roles("admin")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """Frequência de preenchimento do diário familiar × perfil socioeconômico do responsável
    (faixa de renda, monoparentalidade, faixa etária). Restrito a admin — cruza dado sensível
    autodeclarado pelo responsável."""
    return await repo.diary_fill_by_parent_profile(date_from, date_to)


@router.get("/behavior-by-support-level")
@inject
async def behavior_by_support_level(
    date_from: Optional[_date] = None,
    date_to: Optional[_date] = None,
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: MetricsRepository = Depends(Provide[Container.metrics_repository]),
):
    """% de respostas 'Sim' em cada pergunta fechada do diário escolar, por nível de suporte do
    autismo — busca correlação entre nível de suporte e comportamentos registrados."""
    return await repo.behavior_by_support_level(date_from, date_to)
