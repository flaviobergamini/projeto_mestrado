"""update_userrole_enum_values

Revision ID: b1c2d3e4f5a6
Revises: a4b5c6d7e8f9
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME VALUE 'therapist' TO 'secretary'")
    op.execute("ALTER TYPE userrole RENAME VALUE 'parent' TO 'school_admin'")


def downgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME VALUE 'secretary' TO 'therapist'")
    op.execute("ALTER TYPE userrole RENAME VALUE 'school_admin' TO 'parent'")
