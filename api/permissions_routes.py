"""Permissões de acesso (menus/telas do frontend) por perfil, configuráveis pelo admin."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide
from sqlalchemy import select, delete

from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.permissions.roles import ALL_ROLES, ADMIN
from infrastructure.database_context.database import Database
from infrastructure.models.role_permission import RolePermission

router = APIRouter(prefix="/permissions", tags=["Permissions"])


class PermissionsBody(BaseModel):
    allowed: list[str]


@router.get("")
@inject
async def list_permissions(
    current_user: dict = Depends(require_roles("admin")),
    database: Database = Depends(Provide[Container.database]),
):
    """Configuração salva de cada perfil. Perfil ausente = usa o padrão do frontend."""
    async with database.session() as session:
        rows = (await session.execute(select(RolePermission))).scalars().all()
    return {"roles": sorted(ALL_ROLES), "overrides": {r.role: r.allowed for r in rows}}


@router.get("/me")
@inject
async def my_permissions(
    current_user: dict = Depends(get_current_user),
    database: Database = Depends(Provide[Container.database]),
):
    """Itens liberados para o perfil de quem chama; `allowed` nulo = padrão do frontend."""
    if current_user["role"] == ADMIN:
        return {"allowed": None}
    async with database.session() as session:
        row = await session.get(RolePermission, current_user["role"])
    return {"allowed": row.allowed if row else None}


@router.put("/{role}")
@inject
async def save_permissions(
    role: str,
    body: PermissionsBody,
    current_user: dict = Depends(require_roles("admin")),
    database: Database = Depends(Provide[Container.database]),
):
    if role not in ALL_ROLES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil inválido")
    if role == ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O perfil admin sempre tem acesso total")
    allowed = sorted(set(body.allowed))
    async with database.session() as session:
        row = await session.get(RolePermission, role)
        if row:
            row.allowed = allowed
        else:
            session.add(RolePermission(role=role, allowed=allowed))
        await session.commit()
    return {"role": role, "allowed": allowed}


@router.delete("/{role}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def reset_permissions(
    role: str,
    current_user: dict = Depends(require_roles("admin")),
    database: Database = Depends(Provide[Container.database]),
):
    """Volta o perfil ao padrão do código."""
    async with database.session() as session:
        await session.execute(delete(RolePermission).where(RolePermission.role == role))
        await session.commit()
