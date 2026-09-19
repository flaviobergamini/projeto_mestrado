"""create saved_skill_results table

Revision ID: 0026_saved_skill_results
Revises: 0025_fk_composite_idx
Create Date: 2026-09-19

Resultados de skills salvos por aluno. A PoC guarda isso sem filtro por aluno no
servidor (GET /saved-skills não aceita student_id e o cliente filtra por nome) —
aqui a listagem é sempre escopada por student_id no banco.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0026_saved_skill_results'
down_revision: Union[str, Sequence[str], None] = '0025_fk_composite_idx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'saved_skill_results',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(64), sa.ForeignKey('skills.id', ondelete='SET NULL'), nullable=True),
        sa.Column('skill_title', sa.String(255), nullable=False),
        # Texto da resposta da IA (desanonimizado, com nomes reais) — criptografado
        # em repouso como as mensagens de chat (coluna Text guarda o ciphertext Fernet).
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('saved_by_user_id', sa.String(64), nullable=True),
        sa.Column('saved_by_username', sa.String(255), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    # Listagem por aluno (+ skill opcional), mais recentes primeiro.
    op.create_index(
        'ix_saved_skill_results_student_skill_created',
        'saved_skill_results',
        ['student_id', 'skill_id', 'created_at'],
        postgresql_ops={'created_at': 'DESC'},
    )
    op.create_index('ix_saved_skill_results_skill_id', 'saved_skill_results', ['skill_id'])


def downgrade() -> None:
    op.drop_table('saved_skill_results')
