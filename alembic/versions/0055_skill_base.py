"""habilidade / campo de experiência BASE (excludente com a finalística)

Revision ID: 0055_skill_base
Revises: 0054_skill_graphs_drop_fields
Create Date: 2026-11-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0055_skill_base'
down_revision: Union[str, Sequence[str], None] = '0054_skill_graphs_drop_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_skill_scores', sa.Column('is_base', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('student_skill_scores', 'is_base')
