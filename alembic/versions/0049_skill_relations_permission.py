"""permissões: a nova tela "Relações" (skillRelations) herda o nível de "Cadastro" (skillsRegistry) nos perfis já configurados

Perfis com configuração salva não têm a chave nova e ficariam "sem acesso" à tela. Esta migração copia o nível de
"Cadastro" para "Relações" em cada perfil que já tem a configuração; depois disso o administrador ajusta como quiser.
Perfis sem personalização (sem linha) continuam valendo o padrão do código.

Revision ID: 0049_skill_relations_permission
Revises: 0048_skill_relations
Create Date: 2026-11-15
"""
import json
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0049_skill_relations_permission'
down_revision: Union[str, Sequence[str], None] = '0048_skill_relations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_KEY, PARENT_KEY = "skillRelations", "skillsRegistry"


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT role, allowed FROM role_permissions")).fetchall()
    for role, allowed in rows:
        value = json.loads(allowed) if isinstance(allowed, str) else allowed
        changed = False
        if isinstance(value, dict):
            if PARENT_KEY in value and NEW_KEY not in value:
                value[NEW_KEY] = value[PARENT_KEY]
                changed = True
        elif isinstance(value, list):  # formato antigo: lista de telas liberadas
            if PARENT_KEY in value and NEW_KEY not in value:
                value.append(NEW_KEY)
                changed = True
        if changed:
            conn.execute(
                sa.text("UPDATE role_permissions SET allowed = CAST(:v AS JSONB) WHERE role = :r"),
                {"v": json.dumps(value), "r": role},
            )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT role, allowed FROM role_permissions")).fetchall()
    for role, allowed in rows:
        value = json.loads(allowed) if isinstance(allowed, str) else allowed
        if isinstance(value, dict) and NEW_KEY in value:
            value.pop(NEW_KEY)
        elif isinstance(value, list) and NEW_KEY in value:
            value = [k for k in value if k != NEW_KEY]
        else:
            continue
        conn.execute(sa.text("UPDATE role_permissions SET allowed = CAST(:v AS JSONB) WHERE role = :r"),
                     {"v": json.dumps(value), "r": role})
