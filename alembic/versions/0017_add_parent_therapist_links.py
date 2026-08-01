"""Add parent_student_links and therapist_student_links tables

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parent_student_links",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("parent_user_id", sa.String(64), sa.ForeignKey("user_profiles.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False),
        sa.Column("student_id", sa.String(64), sa.ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_psl_parent", "parent_student_links", ["parent_user_id"])
    op.create_index("ix_psl_student", "parent_student_links", ["student_id"])
    op.create_unique_constraint("uq_psl_parent_student", "parent_student_links", ["parent_user_id", "student_id"])

    op.create_table(
        "therapist_student_links",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("therapist_user_id", sa.String(64), sa.ForeignKey("user_profiles.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False),
        sa.Column("student_id", sa.String(64), sa.ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_thl_therapist", "therapist_student_links", ["therapist_user_id"])
    op.create_index("ix_thl_student", "therapist_student_links", ["student_id"])
    op.create_unique_constraint("uq_thl_therapist_student", "therapist_student_links", ["therapist_user_id", "student_id"])


def downgrade() -> None:
    op.drop_table("therapist_student_links")
    op.drop_table("parent_student_links")
