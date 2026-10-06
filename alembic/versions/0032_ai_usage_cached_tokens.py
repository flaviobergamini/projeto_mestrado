"""ai_usage_logs.cached_tokens

Revision ID: 0032_ai_usage_cached
Revises: 0031_functional_profiles
Create Date: 2026-10-05

Quantos tokens de entrada vieram do cache de contexto do Gemini (implícito ou
explícito) em cada chamada — base para medir o ganho e calcular o custo real.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0032_ai_usage_cached'
down_revision: Union[str, Sequence[str], None] = '0031_functional_profiles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_usage_logs', sa.Column('cached_tokens', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('ai_usage_logs', 'cached_tokens')
