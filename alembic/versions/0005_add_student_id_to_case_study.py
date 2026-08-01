"""Add student_id and submitted_by to case_study_submissions

Revision ID: 0005_case_study_student
Revises: 0004_add_teacher_name_pdis
Create Date: 2026-06-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0005_case_study_student'
down_revision: Union[str, Sequence[str], None] = '0004_add_teacher_name_pdis'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('case_study_submissions',
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='SET NULL'), nullable=True))
    op.add_column('case_study_submissions',
        sa.Column('submitted_by', sa.String(255), nullable=True))
    op.create_index('idx_case_study_student_id', 'case_study_submissions', ['student_id'])


def downgrade() -> None:
    op.drop_index('idx_case_study_student_id', 'case_study_submissions')
    op.drop_column('case_study_submissions', 'submitted_by')
    op.drop_column('case_study_submissions', 'student_id')
