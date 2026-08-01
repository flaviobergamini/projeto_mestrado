"""add_profile_columns_to_users

Revision ID: f3b4c5d6e7a8
Revises: e1f2a3b4c5d6
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f3b4c5d6e7a8'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('specialty', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('contact', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('availability', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'availability')
    op.drop_column('users', 'contact')
    op.drop_column('users', 'specialty')
