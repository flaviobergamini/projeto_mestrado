"""create diary table

Revision ID: 68572a580ac4
Revises: 45e4ef002e66
Create Date: 2025-10-18 20:35:56.950104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68572a580ac4'
down_revision: Union[str, Sequence[str], None] = '45e4ef002e66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'diary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('beneficiary_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('diary_date', sa.Date(), nullable=False),

        # Comportamento
        sa.Column('behavior_description', sa.Text(), nullable=True),
        sa.Column('behavior_rating', sa.Integer(), nullable=True),

        # Atividades
        sa.Column('activity_performance', sa.Text(), nullable=True),
        sa.Column('activity_engagement', sa.Integer(), nullable=True),
        sa.Column('completed_activities', sa.Text(), nullable=True),

        # Socialização
        sa.Column('socialization_description', sa.Text(), nullable=True),
        sa.Column('peer_interaction', sa.Integer(), nullable=True),
        sa.Column('adult_interaction', sa.Integer(), nullable=True),

        # Crise
        sa.Column('crisis_occurred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('crisis_description', sa.Text(), nullable=True),
        sa.Column('crisis_trigger', sa.Text(), nullable=True),
        sa.Column('crisis_intervention', sa.Text(), nullable=True),
        sa.Column('crisis_duration_minutes', sa.Integer(), nullable=True),

        # Estado emocional
        sa.Column('emotional_state', sa.String(length=50), nullable=True),
        sa.Column('mood_rating', sa.Integer(), nullable=True),

        # Comunicação
        sa.Column('communication_description', sa.Text(), nullable=True),
        sa.Column('verbal_communication', sa.Integer(), nullable=True),
        sa.Column('non_verbal_communication', sa.Integer(), nullable=True),

        # Autonomia
        sa.Column('autonomy_description', sa.Text(), nullable=True),
        sa.Column('self_care_skills', sa.Integer(), nullable=True),
        sa.Column('task_independence', sa.Integer(), nullable=True),

        # Observações
        sa.Column('general_observations', sa.Text(), nullable=True),
        sa.Column('teacher_suggestions', sa.Text(), nullable=True),
        sa.Column('adaptations_needed', sa.Text(), nullable=True),
        sa.Column('achievements', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['beneficiary_id'], ['beneficiary.id'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE')
    )

    # Criar índices para melhorar performance nas consultas
    op.create_index('ix_diary_beneficiary_id', 'diary', ['beneficiary_id'])
    op.create_index('ix_diary_user_id', 'diary', ['user_id'])
    op.create_index('ix_diary_date', 'diary', ['diary_date'])
    op.create_index('ix_diary_crisis_occurred', 'diary', ['crisis_occurred'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_diary_crisis_occurred', table_name='diary')
    op.drop_index('ix_diary_date', table_name='diary')
    op.drop_index('ix_diary_user_id', table_name='diary')
    op.drop_index('ix_diary_beneficiary_id', table_name='diary')
    op.drop_table('diary')
