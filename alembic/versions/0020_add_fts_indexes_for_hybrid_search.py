"""add_fts_indexes_for_hybrid_search

Revision ID: 0020_fts_hybrid_search
Revises: 0019_chat_session_title_and_pei_sources_json
Create Date: 2026-08-02

"""
from alembic import op

revision: str = '0020_fts_hybrid_search'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_diary_emb_fts
        ON diary_embedding_gemini
        USING gin(to_tsvector('portuguese', content))
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_case_study_emb_fts
        ON case_study_embedding_gemini
        USING gin(to_tsvector('portuguese', content))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_diary_emb_fts")
    op.execute("DROP INDEX IF EXISTS idx_case_study_emb_fts")
