"""create functional_profiles table

Revision ID: 0031_functional_profiles
Revises: 0030_bncc_skills
Create Date: 2026-10-03

Perfil funcional do aluno (avaliação por domínios, gerada por IA a partir dos
resumos do diário e demais documentos, ou preenchida à mão). Cada registro é uma
fotografia do aluno em um período; a série delas forma o perfil temporal.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0031_functional_profiles'
down_revision: Union[str, Sequence[str], None] = '0030_bncc_skills'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'functional_profiles',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=True),
        sa.Column('period_end', sa.Date(), nullable=True),
        sa.Column('origin', sa.String(10), nullable=False, server_default='manual'),
        sa.Column('sources', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by_user_id', sa.String(64), nullable=True),
        sa.Column('created_by_username', sa.String(255), nullable=True),
        sa.Column('edited_by_username', sa.String(255), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_functional_profiles_student_created', 'functional_profiles', ['student_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('functional_profiles')
