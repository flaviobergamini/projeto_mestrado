"""dias da semana em que a habilidade foi trabalhada (card do Kanban)

Revision ID: 0044_kanban_worked_days
Revises: 0043_bncc_year_range
Create Date: 2026-11-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0044_kanban_worked_days'
down_revision: Union[str, Sequence[str], None] = '0043_bncc_year_range'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pei_kanban_cards', sa.Column('worked_days', sa.Text(), nullable=True))  # JSON: ["mon","wed"]


def downgrade() -> None:
    op.drop_column('pei_kanban_cards', 'worked_days')
