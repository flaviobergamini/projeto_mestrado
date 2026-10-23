"""lançamentos do diário da ação (por data, com fotos) nos cards do Kanban

Revision ID: 0038_kanban_entries
Revises: 0037_responsible_teachers
Create Date: 2026-10-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0038_kanban_entries'
down_revision: Union[str, Sequence[str], None] = '0037_responsible_teachers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pei_kanban_entries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('card_id', sa.String(length=64), sa.ForeignKey('pei_kanban_cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False, server_default=''),
        sa.Column('photos', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=120), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_pei_kanban_entries_card_id', 'pei_kanban_entries', ['card_id'])
    # o diário antigo (um texto só, mais as fotos do card) vira o primeiro lançamento, na data da última alteração do card
    op.execute("""
        INSERT INTO pei_kanban_entries (id, card_id, entry_date, text, photos, created_by)
        SELECT gen_random_uuid()::text, id, COALESCE(updated_at, created_at, now())::date, COALESCE(daily_log, ''), photos, created_by
        FROM pei_kanban_cards
        WHERE deleted = false AND (COALESCE(daily_log, '') <> '' OR photos IS NOT NULL)
    """)


def downgrade() -> None:
    op.drop_index('ix_pei_kanban_entries_card_id', table_name='pei_kanban_entries')
    op.drop_table('pei_kanban_entries')
