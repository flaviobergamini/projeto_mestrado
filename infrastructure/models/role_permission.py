from datetime import datetime
from typing import Any
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class RolePermission(Base):
    """Telas que cada perfil acessa e com que nível (configurado pelo admin): dict {tela: "read"|"write"} ou, no formato
    antigo, lista de telas liberadas (ver core/permissions/access_levels.py).
    Sem linha para o perfil = vale o padrão definido no código do frontend."""
    __tablename__ = "role_permissions"

    role: Mapped[str] = mapped_column(String(64), primary_key=True)
    allowed: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
