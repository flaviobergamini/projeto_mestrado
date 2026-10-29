from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database_context.database import Base


class RolePermission(Base):
    """Itens de menu/telas que cada perfil enxerga no frontend (configurado pelo admin).
    Sem linha para o perfil = vale o padrão definido no código do frontend."""
    __tablename__ = "role_permissions"

    role: Mapped[str] = mapped_column(String(64), primary_key=True)
    allowed: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
