"""create diary_summaries table

Revision ID: 0021_create_diary_summaries
Revises: 0020_fts_hybrid_search
Create Date: 2026-09-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0021_create_diary_summaries'
down_revision: Union[str, Sequence[str], None] = '0020_fts_hybrid_search'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'diary_summaries',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('author_user_id', sa.String(64), sa.ForeignKey('user_profiles.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('period_start', sa.String(10), nullable=True),
        sa.Column('period_end', sa.String(10), nullable=True),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('source_entries', sa.JSON(), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_diary_summaries_student_id', 'diary_summaries', ['student_id'])
    op.create_index('ix_diary_summaries_author_user_id', 'diary_summaries', ['author_user_id'])


def downgrade() -> None:
    op.drop_index('ix_diary_summaries_author_user_id', 'diary_summaries')
    op.drop_index('ix_diary_summaries_student_id', 'diary_summaries')
    op.drop_table('diary_summaries')
