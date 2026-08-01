"""add diary_id and beneficiary_id to diary_embedding_gemini

Revision ID: 2542021886dd
Revises: 68572a580ac4
Create Date: 2025-10-18 20:53:36.138219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2542021886dd'
down_revision: Union[str, Sequence[str], None] = '68572a580ac4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adicionar colunas diary_id e beneficiary_id à tabela diary_embedding_gemini
    op.add_column('diary_embedding_gemini',
        sa.Column('diary_id', sa.Integer(), nullable=True)
    )
    op.add_column('diary_embedding_gemini',
        sa.Column('beneficiary_id', sa.Integer(), nullable=True)
    )

    # Adicionar foreign keys
    op.create_foreign_key(
        'fk_diary_embedding_gemini_diary',
        'diary_embedding_gemini', 'diary',
        ['diary_id'], ['id'],
        onupdate='CASCADE', ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_diary_embedding_gemini_beneficiary',
        'diary_embedding_gemini', 'beneficiary',
        ['beneficiary_id'], ['id'],
        onupdate='CASCADE', ondelete='CASCADE'
    )

    # Adicionar índices para melhorar performance
    op.create_index('ix_diary_embedding_gemini_diary_id', 'diary_embedding_gemini', ['diary_id'])
    op.create_index('ix_diary_embedding_gemini_beneficiary_id', 'diary_embedding_gemini', ['beneficiary_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remover índices
    op.drop_index('ix_diary_embedding_gemini_beneficiary_id', table_name='diary_embedding_gemini')
    op.drop_index('ix_diary_embedding_gemini_diary_id', table_name='diary_embedding_gemini')

    # Remover foreign keys
    op.drop_constraint('fk_diary_embedding_gemini_beneficiary', 'diary_embedding_gemini', type_='foreignkey')
    op.drop_constraint('fk_diary_embedding_gemini_diary', 'diary_embedding_gemini', type_='foreignkey')

    # Remover colunas
    op.drop_column('diary_embedding_gemini', 'beneficiary_id')
    op.drop_column('diary_embedding_gemini', 'diary_id')
