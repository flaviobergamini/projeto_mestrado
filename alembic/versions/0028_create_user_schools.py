"""create user_schools table

Revision ID: 0028_user_schools
Revises: 0027_teacher_schools
Create Date: 2026-10-03

Um usuário (professor/coordenação) pode atuar em mais de uma escola.
user_profiles.school_id continua sendo a escola principal; user_schools guarda
TODAS as escolas do usuário, inclusive a principal.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0028_user_schools'
down_revision: Union[str, Sequence[str], None] = '0027_teacher_schools'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_schools',
        sa.Column('user_id', sa.String(64), sa.ForeignKey('user_profiles.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('school_id', sa.String(64), sa.ForeignKey('schools.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_user_schools_school_id', 'user_schools', ['school_id'])
    op.execute(
        "INSERT INTO user_schools (user_id, school_id) "
        "SELECT id, school_id FROM user_profiles WHERE school_id IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_table('user_schools')
