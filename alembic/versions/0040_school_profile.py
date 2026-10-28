"""questionário de cadastro da escola (recursos, equipe, apoio pedagógico etc.) da PoC

Revision ID: 0040_school_profile
Revises: 0039_entry_reaction
Create Date: 2026-10-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0040_school_profile'
down_revision: Union[str, Sequence[str], None] = '0039_entry_reaction'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('schools', sa.Column('profile', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('schools', 'profile')
