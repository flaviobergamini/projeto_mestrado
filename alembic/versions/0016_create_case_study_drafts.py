"""create case_study_drafts table

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_study_drafts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("student_id", sa.String(64), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_study_id", sa.String(64), nullable=True),
        sa.Column("answers", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_cs_drafts_user_student", "case_study_drafts", ["user_id", "student_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_cs_drafts_user_student", "case_study_drafts")
    op.drop_table("case_study_drafts")
