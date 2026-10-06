"""skill plan: quadro por habilidade, histórico, sugestões da IA, resumos mensais e Kanban ligado à habilidade

Revision ID: 0033_skill_plan
Revises: 0032_ai_usage_cached
Create Date: 2026-10-05

- student_skill_scores: adaptação, justificativa, ações, habilidades correlatas, "incluir no plano"
  e "não trabalhar com a IA".
- student_skill_events: histórico de mudanças de nota (e outros marcos) por habilidade.
- skill_suggestions: sugestões da IA (rodada 2) de atualizar a nota, aceitas ou recusadas pela professora.
- skill_monthly_snapshots: memória de médio prazo (resumo do mês por habilidade).
- pei_kanban_cards: ligação com a habilidade, adaptação, registro do dia e data da avaliação pela IA.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0033_skill_plan'
down_revision: Union[str, Sequence[str], None] = '0032_ai_usage_cached'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for col in ('adaptation', 'justification', 'actions', 'correlated_codes'):
        op.add_column('student_skill_scores', sa.Column(col, sa.Text(), nullable=True))
    op.add_column('student_skill_scores', sa.Column('ai_excluded', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('student_skill_scores', sa.Column('in_plan', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('student_skill_scores', sa.Column('plan_ai_at', sa.DateTime(), nullable=True))

    op.create_table(
        'student_skill_events',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(30), nullable=False),
        sa.Column('old_score', sa.SmallInteger(), nullable=True),
        sa.Column('new_score', sa.SmallInteger(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('evidence_card_ids', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(64), nullable=True),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_skill_events_student_skill_created', 'student_skill_events', ['student_id', 'skill_id', 'created_at'])

    op.create_table(
        'skill_suggestions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_score', sa.SmallInteger(), nullable=False),
        sa.Column('suggested_score', sa.SmallInteger(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('evidence_card_ids', sa.Text(), nullable=True),
        sa.Column('status', sa.String(10), nullable=False, server_default='pending'),
        sa.Column('decided_by', sa.String(255), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_skill_suggestions_student_status', 'skill_suggestions', ['student_id', 'status'])

    op.create_table(
        'skill_monthly_snapshots',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('month', sa.String(7), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('end_score', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('student_id', 'skill_id', 'month', name='uq_skill_snapshot_month'),
    )

    op.add_column('pei_kanban_cards', sa.Column('skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='SET NULL'), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('adaptation', sa.Text(), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('daily_log', sa.Text(), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('correlated_codes', sa.Text(), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('score_at_creation', sa.SmallInteger(), nullable=True))
    op.add_column('pei_kanban_cards', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.create_index('ix_pei_kanban_cards_skill_id', 'pei_kanban_cards', ['skill_id'])


def downgrade() -> None:
    op.drop_index('ix_pei_kanban_cards_skill_id', table_name='pei_kanban_cards')
    for col in ('reviewed_at', 'score_at_creation', 'correlated_codes', 'daily_log', 'adaptation', 'skill_id'):
        op.drop_column('pei_kanban_cards', col)
    op.drop_table('skill_monthly_snapshots')
    op.drop_table('skill_suggestions')
    op.drop_table('student_skill_events')
    for col in ('plan_ai_at', 'in_plan', 'ai_excluded', 'correlated_codes', 'actions', 'justification', 'adaptation'):
        op.drop_column('student_skill_scores', col)
