"""create ai_prompts table

Revision ID: 0009_create_ai_prompts
Revises: 0008_alter_encrypted_columns_to_text
Create Date: 2026-07-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0009_create_ai_prompts'
down_revision: Union[str, Sequence[str], None] = '0008_encrypt_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_prompts',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('scope', sa.String(32), nullable=False),
        sa.Column('name', sa.String(120), nullable=False, server_default='Prompt padrão'),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_ai_prompts_scope', 'ai_prompts', ['scope'])


def downgrade() -> None:
    op.drop_index('ix_ai_prompts_scope', 'ai_prompts')
    op.drop_table('ai_prompts')
