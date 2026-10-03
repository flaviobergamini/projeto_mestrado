"""create bncc_skills, student_skill_scores and skill_reports

Revision ID: 0030_bncc_skills
Revises: 0029_diary_questions
Create Date: 2026-10-03

Catálogo de habilidades BNCC (Educação Infantil e Fundamental I, por ano), notas
0-5 por aluno e relatórios guardados em JSON. O catálogo é semeado a partir de
alembic/data/bncc_skills.json e pode ser editado pelo painel.
"""
import json
import uuid
from pathlib import Path
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0030_bncc_skills'
down_revision: Union[str, Sequence[str], None] = '0029_diary_questions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED = Path(__file__).resolve().parent.parent / "data" / "bncc_skills.json"


def upgrade() -> None:
    skills = op.create_table(
        'bncc_skills',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('stage', sa.String(20), nullable=False),
        sa.Column('grade', sa.String(80), nullable=False),
        sa.Column('grade_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('area', sa.String(160), nullable=False),
        sa.Column('code', sa.String(40), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_bncc_skills_grade', 'bncc_skills', ['grade'])
    op.create_index('ix_bncc_skills_grade_code', 'bncc_skills', ['grade', 'code'])

    op.create_table(
        'student_skill_scores',
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('score', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('observation', sa.Text(), nullable=True),
        sa.Column('updated_by_user_id', sa.String(64), nullable=True),
        sa.Column('updated_by_username', sa.String(255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('score >= 0 AND score <= 5', name='ck_student_skill_scores_score'),
    )
    op.create_index('ix_student_skill_scores_skill_id', 'student_skill_scores', ['skill_id'])

    op.create_table(
        'skill_reports',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by_user_id', sa.String(64), nullable=True),
        sa.Column('created_by_username', sa.String(255), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_skill_reports_student_created', 'skill_reports', ['student_id', 'created_at'])

    rows = json.loads(SEED.read_text(encoding='utf-8'))
    op.bulk_insert(skills, [
        {'id': str(uuid.uuid4()), 'stage': r['stage'], 'grade': r['grade'], 'grade_order': r['grade_order'],
         'area': r['area'], 'code': r['code'], 'description': r['description'], 'position': r['position']}
        for r in rows
    ])


def downgrade() -> None:
    op.drop_table('skill_reports')
    op.drop_table('student_skill_scores')
    op.drop_table('bncc_skills')
