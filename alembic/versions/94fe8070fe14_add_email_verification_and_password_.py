"""add_email_verification_and_password_reset_fields

Revision ID: 94fe8070fe14
Revises: 729ce661dd04
Create Date: 2026-01-19 13:12:56.833366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94fe8070fe14'
down_revision: Union[str, Sequence[str], None] = '729ce661dd04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alterar tamanho do campo email de 50 para 254 caracteres
    op.alter_column('users', 'email',
                    existing_type=sa.String(50),
                    type_=sa.String(254),
                    existing_nullable=False)

    # Adicionar novos campos
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remover novos campos
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'email_verified')

    # Reverter tamanho do campo email
    op.alter_column('users', 'email',
                    existing_type=sa.String(254),
                    type_=sa.String(50),
                    existing_nullable=False)
