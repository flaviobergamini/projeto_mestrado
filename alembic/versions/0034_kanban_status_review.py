"""kanban: novos status 'review' (Para avaliação da IA) e 'archived' (Consolidado/Arquivado)

Revision ID: 0034_kanban_status_review
Revises: 0033_skill_plan
Create Date: 2026-10-05
"""
from typing import Sequence, Union
from alembic import op

revision: str = '0034_kanban_status_review'
down_revision: Union[str, Sequence[str], None] = '0033_skill_plan'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('ck_pei_kanban_cards_status', 'pei_kanban_cards', type_='check')
    op.create_check_constraint(
        'ck_pei_kanban_cards_status', 'pei_kanban_cards',
        "status IN ('todo', 'doing', 'review', 'done', 'archived')",
    )


def downgrade() -> None:
    op.execute("UPDATE pei_kanban_cards SET status = 'done' WHERE status IN ('review', 'archived')")
    op.drop_constraint('ck_pei_kanban_cards_status', 'pei_kanban_cards', type_='check')
    op.create_check_constraint('ck_pei_kanban_cards_status', 'pei_kanban_cards', "status IN ('todo', 'doing', 'done')")
