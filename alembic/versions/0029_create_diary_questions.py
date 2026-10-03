"""create diary_questions and diary_entries.custom_answers

Revision ID: 0029_diary_questions
Revises: 0028_user_schools
Create Date: 2026-10-03

Perguntas do diário escolar configuráveis por aluno. Linhas com student_id NULL
são o padrão (as 7 perguntas originais); um aluno sem linhas próprias herda o
padrão. Respostas das perguntas personalizadas ficam em diary_entries.custom_answers
(JSON criptografado, com o texto da pergunta no momento da resposta).
"""
import uuid
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0029_diary_questions'
down_revision: Union[str, Sequence[str], None] = '0028_user_schools'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULTS = [
    ("had_lunch", "Lanchou?"),
    ("participated_in_play", "Participou da brincadeira/atividade coletiva?"),
    ("teacher_attention", "Deu atenção à fala da professora?"),
    ("activity_interest", "Demonstrou interesse para as atividades?"),
    ("completed_activities", "Realizou as atividades propostas?"),
    ("bathroom_use", "Fez uso do banheiro?"),
    ("followed_agreements", "Cumpriu os combinados?"),
]


def upgrade() -> None:
    table = op.create_table(
        'diary_questions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('key', sa.String(64), nullable=False),
        sa.Column('label', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('builtin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_diary_questions_student_position', 'diary_questions', ['student_id', 'position'])
    op.bulk_insert(table, [
        {'id': str(uuid.uuid4()), 'student_id': None, 'key': k, 'label': label, 'position': i, 'builtin': True}
        for i, (k, label) in enumerate(DEFAULTS)
    ])
    op.add_column('diary_entries', sa.Column('custom_answers', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('diary_entries', 'custom_answers')
    op.drop_table('diary_questions')
