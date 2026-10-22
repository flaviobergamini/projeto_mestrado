"""hierarquia de professores por aluno (responsável 1, 2, 3...) e professor responsável nos cards do Kanban

Revision ID: 0037_responsible_teachers
Revises: 0036_kanban_summary_photos
Create Date: 2026-10-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0037_responsible_teachers'
down_revision: Union[str, Sequence[str], None] = '0036_kanban_summary_photos'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('teacher_student_links', sa.Column('rank', sa.SmallInteger(), nullable=True))
    # vínculos que já existem: a ordem em que foram criados vira a hierarquia (1, 2, 3...) de cada aluno
    op.execute("""
        UPDATE teacher_student_links t SET rank = r.rn
        FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY created_at, id) AS rn
              FROM teacher_student_links WHERE deleted = false) r
        WHERE t.id = r.id
    """)
    op.add_column('pei_kanban_cards', sa.Column('responsible_teacher_id', sa.String(length=64), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('responsible_user_id', sa.String(length=64), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('responsible_name', sa.String(length=255), nullable=True))
    op.create_index('ix_pei_kanban_cards_responsible_teacher_id', 'pei_kanban_cards', ['responsible_teacher_id'])


def downgrade() -> None:
    op.drop_index('ix_pei_kanban_cards_responsible_teacher_id', table_name='pei_kanban_cards')
    op.drop_column('pei_kanban_cards', 'responsible_name')
    op.drop_column('pei_kanban_cards', 'responsible_user_id')
    op.drop_column('pei_kanban_cards', 'responsible_teacher_id')
    op.drop_column('teacher_student_links', 'rank')
