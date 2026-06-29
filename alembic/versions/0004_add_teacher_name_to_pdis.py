"""Add teacher_name to pdis table

Revision ID: 0004_add_teacher_name_pdis
Revises: 0003_add_teacher_presence_to_diary
Create Date: 2026-06-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0004_add_teacher_name_pdis'
down_revision: Union[str, Sequence[str], None] = '0003_diary_teacher_presence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pdis', sa.Column('teacher_name', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('pdis', 'teacher_name')
