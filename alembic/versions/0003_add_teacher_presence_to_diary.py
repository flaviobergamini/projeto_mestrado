"""Add teacher_name and presence to diary_entries

Revision ID: 0003_diary_teacher_presence
Revises: 0002_add_birth_date_students
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003_diary_teacher_presence'
down_revision: Union[str, Sequence[str], None] = '0002_add_birth_date_students'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('diary_entries', sa.Column('teacher_name', sa.String(255), nullable=True))
    op.add_column('diary_entries', sa.Column('presence', sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column('diary_entries', 'presence')
    op.drop_column('diary_entries', 'teacher_name')
