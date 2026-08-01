"""add anonymized_data column to students and diary_entries

Revision ID: 0013_add_anonymized_data_columns
Revises: 0012_create_ai_usage_logs
Create Date: 2026-07-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0013_add_anonymized_data_columns'
down_revision: Union[str, Sequence[str], None] = '0012_create_ai_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('anonymized_data', sa.Text(), nullable=True))
    op.add_column('diary_entries', sa.Column('anonymized_data', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('diary_entries', 'anonymized_data')
    op.drop_column('students', 'anonymized_data')
