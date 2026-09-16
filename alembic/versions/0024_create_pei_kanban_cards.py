"""create pei_kanban_cards table

Revision ID: 0024_pei_kanban_cards
Revises: 0023_create_skills
Create Date: 2026-09-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0024_pei_kanban_cards'
down_revision: Union[str, Sequence[str], None] = '0023_create_skills'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pei_kanban_cards',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('pei_id', sa.String(64), sa.ForeignKey('generated_peis.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='todo'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reaction', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(20), nullable=False, server_default='manual'),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.String(120), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    )
    op.create_check_constraint(
        'ck_pei_kanban_cards_status', 'pei_kanban_cards', "status IN ('todo', 'doing', 'done')",
    )
    op.create_check_constraint(
        'ck_pei_kanban_cards_reaction', 'pei_kanban_cards', 'reaction IS NULL OR (reaction >= 1 AND reaction <= 5)',
    )


def downgrade() -> None:
    op.drop_table('pei_kanban_cards')
