"""Leitura (com cache curto) dos níveis de acesso salvos por perfil, usada a cada escrita.

O cache evita uma ida ao banco por requisição; `invalidate()` é chamado quando o admin salva ou restaura um perfil."""
import time
from typing import Optional

from core.permissions.access_levels import normalize_levels
from infrastructure.database_context.database import Database
from infrastructure.models.role_permission import RolePermission

_TTL_SECONDS = 20
_cache: dict[str, tuple[float, Optional[dict[str, str]]]] = {}


def invalidate(role: Optional[str] = None) -> None:
    if role is None:
        _cache.clear()
    else:
        _cache.pop(role, None)


async def levels_for(database: Database, role: str) -> Optional[dict[str, str]]:
    """{tela: "read"|"write"} do perfil, ou None quando o perfil não foi personalizado."""
    hit = _cache.get(role)
    if hit and time.monotonic() - hit[0] < _TTL_SECONDS:
        return hit[1]
    async with database.session() as session:
        row = await session.get(RolePermission, role)
    levels = normalize_levels(row.allowed) if row else None
    _cache[role] = (time.monotonic(), levels)
    return levels
