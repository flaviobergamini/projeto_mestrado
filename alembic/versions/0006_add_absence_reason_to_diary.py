"""add absence_reason to diary_entries

Revision ID: 0006_add_absence_reason_diary
Revises: 0005_case_study_student
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_add_absence_reason_diary'
down_revision = '0005_case_study_student'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('diary_entries', sa.Column('absence_reason', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('diary_entries', 'absence_reason')
