"""resumo (IA) e fotos do diário nos cards do Kanban

Revision ID: 0036_kanban_summary_photos
Revises: 0035_skill_summary
Create Date: 2026-10-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0036_kanban_summary_photos'
down_revision: Union[str, Sequence[str], None] = '0035_skill_summary'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pei_kanban_cards', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('photos', sa.Text(), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('action_id', sa.String(length=64), nullable=True))
    op.create_index('ix_pei_kanban_cards_action_id', 'pei_kanban_cards', ['action_id'])


def downgrade() -> None:
    op.drop_index('ix_pei_kanban_cards_action_id', table_name='pei_kanban_cards')
    op.drop_column('pei_kanban_cards', 'action_id')
    op.drop_column('pei_kanban_cards', 'photos')
    op.drop_column('pei_kanban_cards', 'summary')
