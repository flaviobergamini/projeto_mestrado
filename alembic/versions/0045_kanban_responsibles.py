"""vários professores responsáveis por card do Kanban (lista JSON; as colunas antigas guardam o primeiro)

Revision ID: 0045_kanban_responsibles
Revises: 0044_kanban_worked_days
Create Date: 2026-11-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0045_kanban_responsibles'
down_revision: Union[str, Sequence[str], None] = '0044_kanban_worked_days'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pei_kanban_cards', sa.Column('responsibles', sa.Text(), nullable=True))  # JSON: [{teacher_id, user_id, name}]


def downgrade() -> None:
    op.drop_column('pei_kanban_cards', 'responsibles')
