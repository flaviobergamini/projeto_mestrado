"""Vínculos professor-aluno e visão de relações. Camada HTTP apenas: a regra fica nos use cases."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, require_write
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.links.links_use_cases import (
    ListStudentsWithLinksUseCase, ListLinkableTeachersUseCase, SetStudentTeachersUseCase,
    SetTeacherStudentsUseCase, GetRelationsUseCase,
)

router = APIRouter(prefix="/links", tags=["Links"])

WRITERS = ("admin", "coordenacao")


class SetTeachersBody(BaseModel):
    teacher_ids: list[str]


class SetStudentsBody(BaseModel):
    student_ids: list[str]


def _unwrap(result: Result):
    if result.is_ok:
        return result.value
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.not_found_error)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.bad_request_error or result.error)


@router.get("/students")
@inject
async def list_students_with_links(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    use_case: ListStudentsWithLinksUseCase = Depends(Provide[Container.list_students_with_links_use_case]),
):
    """Lista alunos com seus professores vinculados (paginado)."""
    return _unwrap(await use_case.execute(page, page_size, name))


@router.get("/teachers")
@inject
async def list_teachers(
    current_user: dict = Depends(get_current_user),
    use_case: ListLinkableTeachersUseCase = Depends(Provide[Container.list_linkable_teachers_use_case]),
):
    """Lista todos os professores (para preencher o multiselect)."""
    return _unwrap(await use_case.execute())


@router.put("/students/{student_id}/teachers")
@inject
async def set_student_teachers(
    student_id: str,
    body: SetTeachersBody,
    current_user: dict = Depends(require_write(*WRITERS)),
    use_case: SetStudentTeachersUseCase = Depends(Provide[Container.set_student_teachers_use_case]),
):
    return _unwrap(await use_case.execute(student_id, body.teacher_ids))


@router.put("/teachers/{teacher_id}/students")
@inject
async def set_teacher_students(
    teacher_id: str,
    body: SetStudentsBody,
    current_user: dict = Depends(require_write(*WRITERS)),
    use_case: SetTeacherStudentsUseCase = Depends(Provide[Container.set_teacher_students_use_case]),
):
    return _unwrap(await use_case.execute(teacher_id, body.student_ids))


@router.get("/relations")
@inject
async def relations(
    current_user: dict = Depends(require_write(*WRITERS)),
    use_case: GetRelationsUseCase = Depends(Provide[Container.get_relations_use_case]),
):
    return _unwrap(await use_case.execute())
