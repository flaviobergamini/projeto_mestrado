"""add missing FK indexes + composite index on diary_entries hot path

Revision ID: 0025_fk_composite_idx
Revises: 0024_pei_kanban_cards
Create Date: 2026-09-16

Motivado por uma investigação de performance comparando com a PoC: a PoC indexa
toda coluna FK usada em JOIN/WHERE (ver postgres_repositories.py, bootstrap de
índices). Aqui faltavam 4 colunas FK sem índice, e a query mais quente do
sistema (diário por aluno, filtrado por fonte e ordenado por data) não tinha
um índice composto — cada chamada fazia um index scan por student_id e depois
um sort em memória por diary_date.
"""
from typing import Sequence, Union
from alembic import op

revision: str = '0025_fk_composite_idx'
down_revision: Union[str, Sequence[str], None] = '0024_pei_kanban_cards'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_chat_sessions_created_by_user_id', 'chat_sessions', ['created_by_user_id'])
    op.create_index('ix_chat_sessions_teacher_id', 'chat_sessions', ['teacher_id'])
    op.create_index('ix_chat_messages_user_id', 'chat_messages', ['user_id'])
    op.create_index('ix_user_profiles_teacher_id', 'user_profiles', ['teacher_id'])
    # Cobre o caminho quente de infrastructure/repositories/diary_repository.py::list_by_student:
    # WHERE student_id = ? [AND source = ?] ORDER BY diary_date DESC
    op.create_index(
        'ix_diary_entries_student_source_date',
        'diary_entries',
        ['student_id', 'source', 'diary_date'],
        postgresql_ops={'diary_date': 'DESC'},
    )


def downgrade() -> None:
    op.drop_index('ix_diary_entries_student_source_date', table_name='diary_entries')
    op.drop_index('ix_user_profiles_teacher_id', table_name='user_profiles')
    op.drop_index('ix_chat_messages_user_id', table_name='chat_messages')
    op.drop_index('ix_chat_sessions_teacher_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_created_by_user_id', table_name='chat_sessions')
