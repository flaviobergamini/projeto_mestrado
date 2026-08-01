"""add_therapist_and_parent_to_userrole

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'therapist'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'parent'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # To downgrade, recreate the type without these values.
    op.execute("""
        ALTER TYPE userrole RENAME TO userrole_old;
        CREATE TYPE userrole AS ENUM ('admin', 'secretary', 'school_admin', 'teacher');
        ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::text::userrole;
        DROP TYPE userrole_old;
    """)
