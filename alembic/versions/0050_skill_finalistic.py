"""habilidade/campo de experiência finalístico (a raiz do conjunto de relações); aposenta o "não trabalhar diretamente"

Revision ID: 0050_skill_finalistic
Revises: 0049_skill_relations_permission
Create Date: 2026-11-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0050_skill_finalistic'
down_revision: Union[str, Sequence[str], None] = '0049_skill_relations_permission'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_skill_scores', sa.Column('finalistic', sa.Boolean(), nullable=False, server_default=sa.false()))
    # o antigo "não trabalhar diretamente" deixa de existir: ninguém fica bloqueado de gerar cards
    op.execute("UPDATE student_skill_scores SET indirect_only = false WHERE indirect_only")


def downgrade() -> None:
    op.drop_column('student_skill_scores', 'finalistic')
