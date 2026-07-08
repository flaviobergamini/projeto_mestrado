"""alter encrypted columns to TEXT to fit Fernet ciphertext

Revision ID: 0008_alter_encrypted_columns_to_text
Revises: 0007_create_case_study_embedding_gemini
Create Date: 2026-07-07

"""
from alembic import op
import sqlalchemy as sa

revision = '0008_encrypt_cols'
down_revision = '0007_case_study_embedding'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # diary_entries — all encrypted fields must be TEXT (Fernet tokens are ~100-400 chars)
    for col in [
        'teacher_name',
        'teacher_attention',
        'followed_agreements',
        'activity_interest',
        'had_lunch',
        'participated_in_play',
        'completed_activities',
        'bathroom_use',
        'open_observation',
        'absence_reason',
    ]:
        op.alter_column(
            'diary_entries', col,
            type_=sa.Text(),
            existing_nullable=True,
        )

    # students
    for col in ['name', 'guardians', 'diagnosis', 'notes']:
        op.alter_column(
            'students', col,
            type_=sa.Text(),
            existing_nullable=col != 'name',
        )

    # case_study_submissions
    op.alter_column(
        'case_study_submissions', 'submitted_by',
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        'case_study_submissions', 'answers',
        type_=sa.Text(),
        existing_nullable=True,
    )

    # chat_messages
    for col in ['content', 'username']:
        op.alter_column(
            'chat_messages', col,
            type_=sa.Text(),
            existing_nullable=col != 'content',
        )


def downgrade() -> None:
    # Restore original column types (data may be truncated if ciphertext was stored)
    op.alter_column('diary_entries', 'teacher_name', type_=sa.String(255), existing_nullable=True)
    for col in ['teacher_attention', 'followed_agreements', 'activity_interest',
                'had_lunch', 'participated_in_play', 'completed_activities',
                'bathroom_use']:
        op.alter_column('diary_entries', col, type_=sa.String(20), existing_nullable=True)

    op.alter_column('students', 'name', type_=sa.String(255), existing_nullable=False)
    op.alter_column('students', 'diagnosis', type_=sa.String(255), existing_nullable=True)

    op.alter_column('case_study_submissions', 'submitted_by', type_=sa.String(255), existing_nullable=True)
    op.alter_column('case_study_submissions', 'answers', type_=sa.JSON(), existing_nullable=True)

    op.alter_column('chat_messages', 'username', type_=sa.String(120), existing_nullable=True)
