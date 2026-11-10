"""Quem pode ver cada aluno (escopo por perfil).

  admin / viewer / pesquisador  -> todos os alunos
  secretaria                    -> alunos das escolas do seu município
  coordenacao                   -> alunos das suas escolas
  professor                     -> SOMENTE os alunos vinculados a ele (teacher_student_links)
  parent                        -> os filhos vinculados a ele (parent_student_links)
  therapist                     -> os pacientes vinculados a ele (therapist_student_links)

`guard_student_scope` é uma dependência de rota: confere o `student_id` que vier no caminho, na query ou no corpo JSON.
"""
from typing import Iterable, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import false, select

from api.dependencies import get_current_user
from core.kernel.container import Container
from infrastructure.database_context.database import Database
from infrastructure.models.parent_student_link import ParentStudentLink
from infrastructure.models.school import School
from infrastructure.models.student import Student
from infrastructure.models.teacher_student_link import TeacherStudentLink
from infrastructure.models.therapist_student_link import TherapistStudentLink

SEE_ALL_ROLES = ("admin", "viewer", "pesquisador")
NOT_FOUND = "Aluno não encontrado"


def student_scope_condition(user: dict):
    """Condição SQLAlchemy sobre `Student` com os alunos que o usuário enxerga; None = todos."""
    role = user.get("role")
    if role in SEE_ALL_ROLES:
        return None
    if role == "secretaria":
        municipality = user.get("municipality_id")
        if not municipality:
            return false()
        return Student.school_id.in_(select(School.id).where(School.municipality_id == municipality, School.deleted == False))  # noqa: E712
    if role == "coordenacao":
        schools = user.get("school_ids") or ([user["school_id"]] if user.get("school_id") else [])
        return Student.school_id.in_(schools) if schools else false()
    if role == "professor":
        teacher = user.get("teacher_id")
        if not teacher:
            return false()
        return Student.id.in_(select(TeacherStudentLink.student_id).where(
            TeacherStudentLink.teacher_id == teacher, TeacherStudentLink.deleted == False))  # noqa: E712
    if role == "parent":
        return Student.id.in_(select(ParentStudentLink.student_id).where(
            ParentStudentLink.parent_user_id == user.get("user_id"), ParentStudentLink.deleted == False))  # noqa: E712
    if role == "therapist":
        return Student.id.in_(select(TherapistStudentLink.student_id).where(
            TherapistStudentLink.therapist_user_id == user.get("user_id"), TherapistStudentLink.deleted == False))  # noqa: E712
    return false()


async def accessible_among(database: Database, user: dict, student_ids: Iterable[str]) -> set[str]:
    """Dos ids informados, os que o usuário pode ver."""
    ids = {i for i in student_ids if i}
    if not ids:
        return set()
    condition = student_scope_condition(user)
    if condition is None:
        return ids
    async with database.session() as session:
        rows = await session.execute(select(Student.id).where(Student.id.in_(ids), Student.deleted == False, condition))  # noqa: E712
        return {r[0] for r in rows.all()}


async def can_access_student(database: Database, user: dict, student_id: str) -> bool:
    return student_id in await accessible_among(database, user, [student_id])


async def ensure_student_access(database: Database, user: dict, student_id: Optional[str]) -> None:
    if student_id and not await can_access_student(database, user, student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)


@inject
async def guard_student_scope(
    request: Request,
    current_user: dict = Depends(get_current_user),
    database: Database = Depends(Provide[Container.database]),
) -> None:
    """Dependência de rota: bloqueia o acesso a um aluno que não é do usuário (`student_id` no caminho, query ou corpo JSON)."""
    student_id = request.path_params.get("student_id") or request.query_params.get("student_id")
    if not student_id and request.method in ("POST", "PUT", "PATCH") and "application/json" in request.headers.get("content-type", ""):
        try:
            data = await request.json()
            student_id = data.get("student_id") if isinstance(data, dict) else None
        except Exception:
            student_id = None
    await ensure_student_access(database, current_user, student_id)


def guard_record(param: str, repository_provider):
    """Dependência de rota para rotas com id de um REGISTRO (entrada de diário, estudo de caso, PDI, PEI salvo):
    busca o registro e confere se o aluno dele é do usuário. Registro inexistente passa (o handler devolve 404).

    O repositório é pedido ao container da aplicação (`app.state.container`) na hora da requisição: a dependência é
    criada dentro desta função, e o `container.wire` só injeta `Provide[...]` em funções de nível de módulo (por isso nada de `@inject` aqui)."""
    provider_name = next(name for name, p in Container.providers.items() if p is repository_provider)

    async def _guard(request: Request, current_user: dict = Depends(get_current_user)) -> None:
        record_id = request.path_params.get(param)
        if not record_id:
            return
        container = request.app.state.container
        database = container.database()
        repo = getattr(container, provider_name)()
        record = await repo.get_by_id(record_id)
        if record:
            await ensure_student_access(database, current_user, record.get("student_id"))
    return _guard
