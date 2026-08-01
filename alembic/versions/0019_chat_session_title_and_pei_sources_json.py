"""chat_sessions: replace extra JSON with title column; generated_peis: sources_used Text -> JSON

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── chat_sessions: add title column, migrate data, drop extra ─────────────
    op.add_column(
        "chat_sessions",
        sa.Column("title", sa.String(255), nullable=True),
    )

    op.execute("""
        UPDATE chat_sessions
        SET title = extra->>'title'
        WHERE extra IS NOT NULL
          AND extra->>'title' IS NOT NULL
    """)

    op.drop_column("chat_sessions", "extra")

    # ── generated_peis: convert sources_used from Text (manual JSON) to JSONB ─
    # Step 1: add new jsonb column
    op.add_column(
        "generated_peis",
        sa.Column("sources_used_json", postgresql.JSONB, nullable=True),
    )

    # Step 2: migrate data — parse the text JSON into native JSONB
    op.execute("""
        UPDATE generated_peis
        SET sources_used_json = sources_used::jsonb
        WHERE sources_used IS NOT NULL
          AND sources_used != ''
    """)

    # Step 3: drop old Text column
    op.drop_column("generated_peis", "sources_used")

    # Step 4: rename new column to sources_used
    op.alter_column("generated_peis", "sources_used_json", new_column_name="sources_used")


def downgrade() -> None:
    # ── generated_peis: revert JSONB back to Text ─────────────────────────────
    op.add_column(
        "generated_peis",
        sa.Column("sources_used_text", sa.Text, nullable=True),
    )
    op.execute("""
        UPDATE generated_peis
        SET sources_used_text = sources_used::text
        WHERE sources_used IS NOT NULL
    """)
    op.drop_column("generated_peis", "sources_used")
    op.alter_column("generated_peis", "sources_used_text", new_column_name="sources_used")

    # ── chat_sessions: restore extra column ───────────────────────────────────
    op.add_column(
        "chat_sessions",
        sa.Column("extra", postgresql.JSONB, nullable=True),
    )
    op.execute("""
        UPDATE chat_sessions
        SET extra = jsonb_build_object('title', title)
        WHERE title IS NOT NULL
    """)
    op.drop_column("chat_sessions", "title")
