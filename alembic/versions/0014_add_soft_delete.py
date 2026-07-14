"""add soft delete column to all main entity tables

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013_add_anonymized_data_columns"
branch_labels = None
depends_on = None

TABLES = [
    "students",
    "schools",
    "teachers",
    "user_profiles",
    "municipalities",
    "diary_entries",
    "case_study_submissions",
    "pdis",
    "generated_peis",
    "chat_sessions",
    "ai_prompts",
    "teacher_student_links",
    "object_storage_files",
    "school_registration_submissions",
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column("deleted", sa.Boolean(), nullable=False, server_default="false"),
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_column(table, "deleted")
