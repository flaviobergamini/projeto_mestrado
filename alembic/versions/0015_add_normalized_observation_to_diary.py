"""add normalized_observation column to diary_entries

Revision ID: 0015_add_normalized_observation_to_diary
Revises: 0014
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "diary_entries",
        sa.Column("normalized_observation", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("diary_entries", "normalized_observation")
