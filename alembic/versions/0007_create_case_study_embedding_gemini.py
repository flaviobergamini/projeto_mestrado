"""create case_study_embedding_gemini table

Revision ID: 0007_case_study_embedding
Revises: 0006_add_absence_reason_diary
Create Date: 2026-07-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import pgvector

revision: str = '0007_case_study_embedding'
down_revision: Union[str, Sequence[str], None] = '0006_add_absence_reason_diary'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'case_study_embedding_gemini',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('case_study_id', sa.String(64),
                  sa.ForeignKey('case_study_submissions.id', ondelete='CASCADE', onupdate='CASCADE'),
                  nullable=False, index=True),
        sa.Column('student_id', sa.String(64),
                  sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'),
                  nullable=True, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )

    # Also ensure diary_embedding_gemini exists (created in 0001 but dropped before it — re-create if needed)
    op.execute("""
        CREATE TABLE IF NOT EXISTS diary_embedding_gemini (
            id SERIAL PRIMARY KEY,
            diary_entry_id VARCHAR(64) REFERENCES diary_entries(id) ON DELETE CASCADE ON UPDATE CASCADE,
            student_id VARCHAR(64) REFERENCES students(id) ON DELETE CASCADE ON UPDATE CASCADE,
            content TEXT,
            meta_data JSON,
            embedding vector(768),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_diary_embedding_gemini_diary_entry_id ON diary_embedding_gemini(diary_entry_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_diary_embedding_gemini_student_id ON diary_embedding_gemini(student_id)")


def downgrade() -> None:
    op.drop_table('case_study_embedding_gemini')
