"""rename_userrole_enum_values

Revision ID: a4b5c6d7e8f9
Revises: f3b4c5d6e7a8
Create Date: 2026-04-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'a4b5c6d7e8f9'
down_revision: Union[str, None] = 'f3b4c5d6e7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum já criado com valores em inglês na migration anterior — nada a fazer
    pass


def downgrade() -> None:
    pass
