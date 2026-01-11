"""create_pei_and_pei_embedding_gemini_tables

Revision ID: a1b2c3d4e5f6
Revises: fa4ed68a894e
Create Date: 2026-01-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fa4ed68a894e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Criar tabela PEI
    op.create_table(
        'pei',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('beneficiary_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('pei_data', sa.JSON(), nullable=False),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['beneficiary_id'], ['beneficiary.id'],
            onupdate='CASCADE', ondelete='CASCADE'
        )
    )

    op.create_index(op.f('ix_pei_id'), 'pei', ['id'], unique=False)
    op.create_index('ix_pei_beneficiary_id', 'pei', ['beneficiary_id'])

    # Criar tabela PEI_Embedding_Gemini
    op.create_table(
        'pei_embedding_gemini',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pei_id', sa.Integer(), nullable=False),
        sa.Column('beneficiary_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['pei_id'], ['pei.id'],
            onupdate='CASCADE', ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['beneficiary_id'], ['beneficiary.id'],
            onupdate='CASCADE', ondelete='CASCADE'
        )
    )

    op.create_index(op.f('ix_pei_embedding_gemini_id'), 'pei_embedding_gemini', ['id'], unique=False)
    op.create_index('ix_pei_embedding_gemini_pei_id', 'pei_embedding_gemini', ['pei_id'])
    op.create_index('ix_pei_embedding_gemini_beneficiary_id', 'pei_embedding_gemini', ['beneficiary_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remover tabela PEI_Embedding_Gemini primeiro (por causa da FK)
    op.drop_index('ix_pei_embedding_gemini_beneficiary_id', table_name='pei_embedding_gemini')
    op.drop_index('ix_pei_embedding_gemini_pei_id', table_name='pei_embedding_gemini')
    op.drop_index(op.f('ix_pei_embedding_gemini_id'), table_name='pei_embedding_gemini')
    op.drop_table('pei_embedding_gemini')

    # Remover tabela PEI
    op.drop_index('ix_pei_beneficiary_id', table_name='pei')
    op.drop_index(op.f('ix_pei_id'), table_name='pei')
    op.drop_table('pei')
