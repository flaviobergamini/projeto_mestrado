"""Permissões de acesso por perfil, configuráveis pelo admin: para cada tela, sem acesso, somente ver ou ver e editar."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide
from sqlalchemy import select, delete

from api.dependencies import get_current_user, require_roles
from api.permission_levels import invalidate, levels_for
from core.kernel.container import Container
from core.permissions.access_levels import normalize_levels, READ, WRITE
from core.permissions.roles import ALL_ROLES, ADMIN
from infrastructure.database_context.database import Database
from infrastructure.models.role_permission import RolePermission

router = APIRouter(prefix="/permissions", tags=["Permissions"])


class PermissionsBody(BaseModel):
    levels: Optional[dict[str, str]] = None  # {tela: "read" | "write"}; tela fora do mapa = sem acesso
    allowed: Optional[list[str]] = None      # formato antigo (só ver/ocultar): cada tela vale como "write"


@router.get("")
@inject
async def list_permissions(
    current_user: dict = Depends(require_roles("admin")),
    database: Database = Depends(Provide[Container.database]),
):
    """Configuração salva de cada perfil ({tela: nível}). Perfil ausente = usa o padrão do frontend."""
    async with database.session() as session:
        rows = (await session.execute(select(RolePermission))).scalars().all()
    return {"roles": sorted(ALL_ROLES), "overrides": {r.role: normalize_levels(r.allowed) for r in rows}}


@router.get("/me")
@inject
async def my_permissions(
    current_user: dict = Depends(get_current_user),
    database: Database = Depends(Provide[Container.database]),
):
    """Telas liberadas para o perfil de quem chama; nulo = padrão do frontend.
    `allowed` = telas que o perfil enxerga; `levels` = {tela: "read" | "write"}."""
    if current_user["role"] == ADMIN:
        return {"allowed": None, "levels": None}
    levels = await levels_for(database, current_user["role"])
    return {"allowed": sorted(levels) if levels is not None else None, "levels": levels}


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
    if body.levels is None and body.allowed is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe os níveis de acesso")
    invalid = [v for v in (body.levels or {}).values() if v not in (READ, WRITE)]
    if invalid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Nível inválido: use "read" ou "write"')
    levels = dict(sorted(body.levels.items())) if body.levels is not None else {k: WRITE for k in sorted(set(body.allowed))}
    async with database.session() as session:
        row = await session.get(RolePermission, role)
        if row:
            row.allowed = levels
        else:
            session.add(RolePermission(role=role, allowed=levels))
        await session.commit()
    invalidate(role)
    return {"role": role, "levels": levels}


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
    invalidate(role)
