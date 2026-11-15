"""relações entre habilidades (habilidade → outra habilidade ou campo de experiência) e marca "não trabalhar diretamente"

Revision ID: 0048_skill_relations
Revises: 0047_student_document_chunks
Create Date: 2026-11-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0048_skill_relations'
down_revision: Union[str, Sequence[str], None] = '0047_student_document_chunks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_skill_scores', sa.Column('indirect_only', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        'student_skill_relations',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(10), nullable=False),
        sa.Column('related_skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('field_key', sa.String(40), nullable=True),
        sa.Column('adaptation', sa.Text(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('actions', sa.Text(), nullable=True),
        sa.Column('source', sa.String(10), nullable=False, server_default='manual'),
        sa.Column('created_by', sa.String(120), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('ix_student_skill_relations_student_id', 'student_skill_relations', ['student_id'])
    op.create_index('ix_student_skill_relations_student_skill', 'student_skill_relations', ['student_id', 'skill_id'])


def downgrade() -> None:
    op.drop_index('ix_student_skill_relations_student_skill', table_name='student_skill_relations')
    op.drop_index('ix_student_skill_relations_student_id', table_name='student_skill_relations')
    op.drop_table('student_skill_relations')
    op.drop_column('student_skill_scores', 'indirect_only')
