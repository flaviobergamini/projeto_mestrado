"""permissões de menu por perfil, configuráveis pelo administrador

Revision ID: 0041_role_permissions
Revises: 0040_school_profile
Create Date: 2026-10-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0041_role_permissions'
down_revision: Union[str, Sequence[str], None] = '0040_school_profile'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'role_permissions',
        sa.Column('role', sa.String(64), primary_key=True),
        sa.Column('allowed', postgresql.JSONB(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('role_permissions')
