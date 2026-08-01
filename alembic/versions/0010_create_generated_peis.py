"""create generated_peis table

Revision ID: 0010_create_generated_peis
Revises: 0009_create_ai_prompts
Create Date: 2026-07-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0010_create_generated_peis'
down_revision: Union[str, Sequence[str], None] = '0009_create_ai_prompts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'generated_peis',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_name', sa.String(120), nullable=False),
        sa.Column('pei_text', sa.Text(), nullable=False),
        sa.Column('sources_used', sa.Text(), nullable=True),
        sa.Column('generated_by', sa.String(64), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_generated_peis_student_id', 'generated_peis', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_generated_peis_student_id', 'generated_peis')
    op.drop_table('generated_peis')
