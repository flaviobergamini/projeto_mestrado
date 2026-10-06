"""Endpoints para gerenciamento de vínculos professor-aluno."""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, require_write
from core.kernel.container import Container
from infrastructure.repositories.vinculos_repository import VinculosRepository
from infrastructure.repositories.teacher_repository import TeacherRepository

router = APIRouter(prefix="/vinculos", tags=["Vínculos"])


class SetTeachersBody(BaseModel):
    teacher_ids: list[str]


@router.get("/students")
@inject
async def list_students_with_links(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    repo: VinculosRepository = Depends(Provide[Container.vinculos_repository]),
):
    """Lista alunos com seus professores vinculados (paginado, filtro por nome em Python)."""
    return await repo.list_students_with_links(page=page, page_size=page_size, name_filter=name)


@router.get("/teachers")
@inject
async def list_teachers(
    current_user: dict = Depends(get_current_user),
    repo: TeacherRepository = Depends(Provide[Container.teacher_repository]),
):
    """Lista todos os professores (para preencher o multiselect)."""
    return await repo.list_all()


@router.put("/students/{student_id}/teachers")
@inject
async def set_student_teachers(
    student_id: str,
    body: SetTeachersBody,
    current_user: dict = Depends(require_write("admin", "coordenacao")),
    repo: VinculosRepository = Depends(Provide[Container.vinculos_repository]),
):
    """Substitui todos os vínculos de professores de um aluno."""
    ok = await repo.set_student_teachers(student_id=student_id, teacher_ids=body.teacher_ids)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    return {"ok": True}


class SetStudentsBody(BaseModel):
    student_ids: list[str]


@router.get("/relations")
@inject
async def relations(
    current_user: dict = Depends(require_write("admin", "coordenacao")),
    repo: VinculosRepository = Depends(Provide[Container.vinculos_repository]),
):
    """Escolas por município, professores por escola (com alunos) e alunos por escola/professor."""
    return await repo.relations()


@router.put("/teachers/{teacher_id}/students")
@inject
async def set_teacher_students(
    teacher_id: str,
    body: SetStudentsBody,
    current_user: dict = Depends(require_write("admin", "coordenacao")),
    repo: VinculosRepository = Depends(Provide[Container.vinculos_repository]),
):
    """Substitui os alunos vinculados a um professor."""
    if not await repo.set_teacher_students(teacher_id, body.student_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")
    return {"ok": True}
