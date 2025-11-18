"""create_study_case_embedding_gemini_table

Revision ID: b5534522224d
Revises: 2542021886dd
Create Date: 2025-11-18 18:56:28.246052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector

revision: str = 'b5534522224d'
down_revision: Union[str, Sequence[str], None] = '2542021886dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'study_case_embedding_gemini',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('beneficiary_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['beneficiary_id'], ['beneficiary.id'],
            onupdate='CASCADE', ondelete='CASCADE'
        )
    )

    op.create_index(op.f('ix_study_case_embedding_gemini_id'), 'study_case_embedding_gemini', ['id'], unique=False)
    op.create_index('ix_study_case_embedding_gemini_beneficiary_id', 'study_case_embedding_gemini', ['beneficiary_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_study_case_embedding_gemini_beneficiary_id', table_name='study_case_embedding_gemini')
    op.drop_index(op.f('ix_study_case_embedding_gemini_id'), table_name='study_case_embedding_gemini')
    op.drop_table('study_case_embedding_gemini')
