"""add_role_to_users

Revision ID: e1f2a3b4c5d6
Revises: 94fe8070fe14
Create Date: 2026-04-04 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userrole_enum = sa.Enum('admin', 'therapist', 'teacher', 'parent', name='userrole')


def upgrade() -> None:
    userrole_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'users',
        sa.Column('role', userrole_enum, nullable=False, server_default='parent')
    )


def downgrade() -> None:
    op.drop_column('users', 'role')
    userrole_enum.drop(op.get_bind(), checkfirst=True)
