"""anexos (PDFs) por aluno, com legenda

Revision ID: 0046_student_documents
Revises: 0045_kanban_responsibles
Create Date: 2026-11-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0046_student_documents'
down_revision: Union[str, Sequence[str], None] = '0045_kanban_responsibles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'student_documents',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('caption', sa.String(255), nullable=False, server_default=''),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(120), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('bucket', sa.String(128), nullable=False),
        sa.Column('object_key', sa.String(512), nullable=False),
        sa.Column('uploaded_by', sa.String(64), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_student_documents_student_id', 'student_documents', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_student_documents_student_id', table_name='student_documents')
    op.drop_table('student_documents')
