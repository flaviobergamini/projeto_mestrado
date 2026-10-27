"""reação do aluno por lançamento do diário da ação

Revision ID: 0039_entry_reaction
Revises: 0038_kanban_entries
Create Date: 2026-10-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0039_entry_reaction'
down_revision: Union[str, Sequence[str], None] = '0038_kanban_entries'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pei_kanban_entries', sa.Column('reaction', sa.SmallInteger(), nullable=True))
    # a reação que ficava no card passa para o lançamento mais recente do mesmo card (quando houver)
    op.execute("""
        UPDATE pei_kanban_entries e SET reaction = c.reaction
        FROM pei_kanban_cards c
        WHERE e.card_id = c.id AND c.reaction IS NOT NULL
          AND e.id = (SELECT e2.id FROM pei_kanban_entries e2 WHERE e2.card_id = c.id
                      ORDER BY e2.entry_date DESC, e2.created_at DESC LIMIT 1)
    """)


def downgrade() -> None:
    op.drop_column('pei_kanban_entries', 'reaction')
