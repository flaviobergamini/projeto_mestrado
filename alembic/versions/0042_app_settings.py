"""configurações gerais ajustáveis pelo administrador (ex.: limites de adaptações e ações geradas pela IA)

Revision ID: 0042_app_settings
Revises: 0041_role_permissions
Create Date: 2026-10-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0042_app_settings'
down_revision: Union[str, Sequence[str], None] = '0041_role_permissions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('app_settings')
