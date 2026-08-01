"""Add birth_date column to students table

Revision ID: 0002_add_birth_date_students
Revises: 0001_rebuild_poc
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_add_birth_date_students'
down_revision: Union[str, Sequence[str], None] = '0001_rebuild_poc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('students', sa.Column('diagnosis', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('students', 'diagnosis')
    op.drop_column('students', 'birth_date')
