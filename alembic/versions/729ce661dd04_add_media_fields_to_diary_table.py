"""add_media_fields_to_diary_table

Revision ID: 729ce661dd04
Revises: a1b2c3d4e5f6
Create Date: 2026-01-13 22:45:10.054077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '729ce661dd04'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adicionar campos de mídia (fotos e vídeos) ao diário
    op.add_column('diary', sa.Column('photos', sa.JSON(), nullable=True))
    op.add_column('diary', sa.Column('videos', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remover campos de mídia
    op.drop_column('diary', 'videos')
    op.drop_column('diary', 'photos')
