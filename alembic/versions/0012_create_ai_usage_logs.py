"""create ai_usage_logs table

Revision ID: 0012_create_ai_usage_logs
Revises: 0011_create_audit_logs
Create Date: 2026-07-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0012_create_ai_usage_logs'
down_revision: Union[str, Sequence[str], None] = '0011_create_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_usage_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('model', sa.String(120), nullable=False),
        sa.Column('operation', sa.String(64), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('user_id', sa.String(64), nullable=True),
        sa.Column('username', sa.String(120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_ai_usage_logs_model', 'ai_usage_logs', ['model'])
    op.create_index('ix_ai_usage_logs_operation', 'ai_usage_logs', ['operation'])
    op.create_index('ix_ai_usage_logs_user_id', 'ai_usage_logs', ['user_id'])
    op.create_index('ix_ai_usage_logs_created_at', 'ai_usage_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_ai_usage_logs_created_at', 'ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_user_id', 'ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_operation', 'ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_model', 'ai_usage_logs')
    op.drop_table('ai_usage_logs')
