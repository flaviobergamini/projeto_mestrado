"""Admin endpoints: user CRUD, pre-registration summary, audit logs."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide
from sqlalchemy import select, func

from api.dependencies import require_roles
from core.kernel.container import Container
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException
from domain.schema import UpdateOwnDemographics
from infrastructure.database_context.database import Database
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.audit_repository import AuditRepository
from infrastructure.models.school import School
from infrastructure.models.teacher import Teacher
from infrastructure.models.student import Student
from infrastructure.models.municipality import Municipality

router = APIRouter(prefix="/admin", tags=["Admin"])


class UserUpdateBody(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    email: Optional[str] = None


# ── Users ──────────────────────────────────────────────────────────────────────

@router.get("/users/by-role/{role}")
@inject
async def list_users_by_role(
    role: str,
    current_user: dict = Depends(require_roles("admin")),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    return await user_repo.list_by_role(role)


@router.get("/users")
@inject
async def list_users_paginated(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin")),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    return await user_repo.list_paginated(page=page, page_size=page_size)


@router.patch("/users/{user_id}")
@inject
async def update_user(
    user_id: str,
    body: UserUpdateBody,
    current_user: dict = Depends(require_roles("admin")),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
    auth_service: IAuthService = Depends(Provide[Container.cognito_service]),
):
    if body.email:
        existing = await user_repo.get_by_id(user_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
        new_email = body.email.strip().lower()
        if new_email != existing["username"]:
            # Cognito primeiro: se o e-mail já estiver em uso (AliasExistsException),
            # falha aqui e o perfil local fica intacto — sem essa ordem, um e-mail
            # duplicado deixaria o perfil local apontando pra um login que o
            # Cognito não reconhece.
            try:
                auth_service.update_email(existing["username"], new_email)
            except AuthException as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            await user_repo.update_username(user_id, new_email)

    updated = await user_repo.update(user_id, full_name=body.full_name, role=body.role, is_active=body.is_active)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return updated


@router.put("/users/{user_id}/demographics")
@inject
async def update_user_demographics(
    user_id: str,
    body: UpdateOwnDemographics,
    current_user: dict = Depends(require_roles("admin")),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    """Admin preenche a demografia do responsável (faixa de renda, monoparentalidade,
    faixa etária, nº de filhos) em nome dele — ex.: coleta feita presencialmente ou
    por telefone. Mesmos campos de PUT /auth/me/demographics (autodeclaração do
    próprio pai), mas sem exigir `consent`: aqui a responsabilidade de ter obtido
    consentimento do responsável é de quem está preenchendo (o admin)."""
    data = body.model_dump(exclude={"consent"}, exclude_unset=True)
    updated = await user_repo.update_demographics(user_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return updated


@router.delete("/users/{user_id}", status_code=204)
@inject
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_roles("admin")),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
    auth_service: IAuthService = Depends(Provide[Container.cognito_service]),
):
    if user_id == current_user.get("user_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não é possível apagar o próprio usuário.")
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    # Remove do Cognito primeiro; se falhar, o banco permanece intacto
    auth_service.delete_user(user["username"])
    await user_repo.delete(user_id)


# ── Pre-registration summary ────────────────────────────────────────────────────

@router.get("/pre-registrations")
@inject
async def pre_registrations(
    current_user: dict = Depends(require_roles("admin")),
    database: Database = Depends(Provide[Container.database]),
):
    """Returns paginated lists of schools, teachers and students with municipality context."""
    async with database.session() as session:
        # Schools with municipality name
        school_rows = await session.execute(
            select(School, Municipality.name.label("municipality_name"))
            .outerjoin(Municipality, School.municipality_id == Municipality.id)
            .where(School.deleted == False)  # noqa: E712
            .order_by(School.name)
        )
        schools = [
            {
                "id": s.id,
                "name": s.name,
                "municipality_id": s.municipality_id,
                "municipality_name": mname,
            }
            for s, mname in school_rows.all()
        ]

        # Teachers with school + municipality
        teacher_rows = await session.execute(
            select(Teacher, School.name.label("school_name"), Municipality.name.label("municipality_name"))
            .outerjoin(School, Teacher.school_id == School.id)
            .outerjoin(Municipality, School.municipality_id == Municipality.id)
            .where(Teacher.deleted == False)  # noqa: E712
            .order_by(Teacher.name)
        )
        teachers = [
            {
                "id": t.id,
                "name": t.name,
                "school_id": t.school_id,
                "school_name": sname,
                "municipality_name": mname,
            }
            for t, sname, mname in teacher_rows.all()
        ]

        # Students with school name
        student_rows = await session.execute(
            select(Student, School.name.label("school_name"))
            .outerjoin(School, Student.school_id == School.id)
            .where(Student.deleted == False)  # noqa: E712
            .order_by(Student.name)
        )
        students = [
            {
                "id": s.id,
                "name": s.name,
                "school_id": s.school_id,
                "school_name": sname,
                "grade": s.grade,
            }
            for s, sname in student_rows.all()
        ]

    return {"schools": schools, "teachers": teachers, "students": students}


# ── Audit logs ─────────────────────────────────────────────────────────────────

@router.get("/audit-logs")
@inject
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin")),
    audit_repo: AuditRepository = Depends(Provide[Container.audit_repository]),
):
    return await audit_repo.list_paginated(page=page, page_size=page_size)
