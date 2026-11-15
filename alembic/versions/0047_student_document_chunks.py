"""anexos: estado do processamento e trechos anonimizados com embedding (RAG)

Revision ID: 0047_student_document_chunks
Revises: 0046_student_documents
Create Date: 2026-11-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy

revision: str = '0047_student_document_chunks'
down_revision: Union[str, Sequence[str], None] = '0046_student_documents'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_documents', sa.Column('status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('student_documents', sa.Column('status_detail', sa.String(255), nullable=True))
    op.add_column('student_documents', sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('student_documents', sa.Column('processed_at', sa.DateTime(), nullable=True))

    op.create_table(
        'student_document_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.String(64), sa.ForeignKey('student_documents.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_student_document_chunks_document_id', 'student_document_chunks', ['document_id'])
    op.create_index('ix_student_document_chunks_student_id', 'student_document_chunks', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_student_document_chunks_student_id', table_name='student_document_chunks')
    op.drop_index('ix_student_document_chunks_document_id', table_name='student_document_chunks')
    op.drop_table('student_document_chunks')
    for col in ('processed_at', 'chunk_count', 'status_detail', 'status'):
        op.drop_column('student_documents', col)
