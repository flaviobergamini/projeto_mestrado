"""create_institution_embedding_gemini_table

Revision ID: fa4ed68a894e
Revises: b5534522224d
Create Date: 2025-11-18 19:38:26.892300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


revision: str = 'fa4ed68a894e'
down_revision: Union[str, Sequence[str], None] = 'b5534522224d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'institution_embedding_gemini',
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

    op.create_index(op.f('ix_institution_embedding_gemini_id'), 'institution_embedding_gemini', ['id'], unique=False)
    op.create_index('ix_institution_embedding_gemini_beneficiary_id', 'institution_embedding_gemini', ['beneficiary_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_institution_embedding_gemini_beneficiary_id', table_name='institution_embedding_gemini')
    op.drop_index(op.f('ix_institution_embedding_gemini_id'), table_name='institution_embedding_gemini')
    op.drop_table('institution_embedding_gemini')
