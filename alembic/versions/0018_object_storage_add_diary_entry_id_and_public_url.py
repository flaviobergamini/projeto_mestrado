"""Add diary_entry_id and public_url columns to object_storage_files; migrate data from extra JSON; drop extra column

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new columns (nullable initially so existing rows don't break)
    op.add_column(
        "object_storage_files",
        sa.Column("diary_entry_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "object_storage_files",
        sa.Column("public_url", sa.String(1024), nullable=True),
    )

    # 2. Migrate data from extra JSON to new columns (only for diary_image rows)
    op.execute("""
        UPDATE object_storage_files
        SET
            diary_entry_id = extra->>'diary_entry_id',
            public_url     = extra->>'public_url'
        WHERE doc_type = 'diary_image'
          AND extra IS NOT NULL
    """)

    # 3. Add FK constraint on diary_entry_id
    op.create_foreign_key(
        "fk_object_storage_diary_entry",
        "object_storage_files",
        "diary_entries",
        ["diary_entry_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. Add index for fast lookups by diary_entry_id
    op.create_index(
        "ix_object_storage_diary_entry_id",
        "object_storage_files",
        ["diary_entry_id"],
    )

    # 5. Drop the extra column
    op.drop_column("object_storage_files", "extra")


def downgrade() -> None:
    # Re-add extra column
    op.add_column(
        "object_storage_files",
        sa.Column("extra", sa.JSON(), nullable=True),
    )

    # Restore data back to extra JSON
    op.execute("""
        UPDATE object_storage_files
        SET extra = jsonb_build_object(
            'diary_entry_id', diary_entry_id,
            'public_url',     public_url
        )
        WHERE doc_type = 'diary_image'
          AND diary_entry_id IS NOT NULL
    """)

    op.drop_index("ix_object_storage_diary_entry_id", table_name="object_storage_files")
    op.drop_constraint("fk_object_storage_diary_entry", "object_storage_files", type_="foreignkey")
    op.drop_column("object_storage_files", "public_url")
    op.drop_column("object_storage_files", "diary_entry_id")
