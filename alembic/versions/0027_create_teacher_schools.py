"""create teacher_schools table

Revision ID: 0027_teacher_schools
Revises: 0026_saved_skill_results
Create Date: 2026-10-03

Um professor pode atuar em mais de uma escola. teachers.school_id continua
existindo como escola principal (consumida por métricas, anonimização e escopo);
teacher_schools guarda TODAS as escolas do professor, inclusive a principal.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0027_teacher_schools'
down_revision: Union[str, Sequence[str], None] = '0026_saved_skill_results'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'teacher_schools',
        sa.Column('teacher_id', sa.String(64), sa.ForeignKey('teachers.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('school_id', sa.String(64), sa.ForeignKey('schools.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_teacher_schools_school_id', 'teacher_schools', ['school_id'])
    # Backfill: a escola única atual de cada professor vira seu primeiro vínculo.
    op.execute(
        "INSERT INTO teacher_schools (teacher_id, school_id) "
        "SELECT id, school_id FROM teachers WHERE school_id IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_table('teacher_schools')
