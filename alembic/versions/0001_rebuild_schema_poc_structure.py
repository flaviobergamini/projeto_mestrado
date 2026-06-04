"""Rebuild schema: replace old tables with PoC structure (expanded payload columns, English column names, CASCADE FK)

Revision ID: 0001_rebuild_poc
Revises: c2d3e4f5a6b7
Create Date: 2026-06-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = '0001_rebuild_poc'
down_revision: Union[str, Sequence[str], None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Drop all old tables (reverse FK order)                           #
    # ------------------------------------------------------------------ #
    op.execute("DROP TABLE IF EXISTS study_case_embedding_gemini CASCADE")
    op.execute("DROP TABLE IF EXISTS pei_embedding_gemini CASCADE")
    op.execute("DROP TABLE IF EXISTS pei CASCADE")
    op.execute("DROP TABLE IF EXISTS institution_embedding_gemini CASCADE")
    op.execute("DROP TABLE IF EXISTS diary_embedding_gemini CASCADE")
    op.execute("DROP TABLE IF EXISTS diary_embedding_groq CASCADE")
    op.execute("DROP TABLE IF EXISTS diary_embedding CASCADE")
    op.execute("DROP TABLE IF EXISTS diary CASCADE")
    op.execute("DROP TABLE IF EXISTS messages CASCADE")
    op.execute("DROP TABLE IF EXISTS conversations CASCADE")
    op.execute("DROP TABLE IF EXISTS audit CASCADE")
    op.execute("DROP TABLE IF EXISTS school_feedback CASCADE")
    op.execute("DROP TABLE IF EXISTS family_reunion CASCADE")
    op.execute("DROP TABLE IF EXISTS therapeutic_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS therapeutic_plan CASCADE")
    op.execute("DROP TABLE IF EXISTS evaluation CASCADE")
    op.execute("DROP TABLE IF EXISTS beneficiary_clinic CASCADE")
    op.execute("DROP TABLE IF EXISTS user_beneficiary CASCADE")
    op.execute("DROP TABLE IF EXISTS beneficiary CASCADE")
    op.execute("DROP TABLE IF EXISTS professional CASCADE")
    op.execute("DROP TABLE IF EXISTS supervisor CASCADE")
    op.execute("DROP TABLE IF EXISTS autismia CASCADE")
    op.execute("DROP TABLE IF EXISTS health_plan CASCADE")
    op.execute("DROP TABLE IF EXISTS school CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")

    # ------------------------------------------------------------------ #
    # 2. Ensure pgvector extension exists                                 #
    # ------------------------------------------------------------------ #
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ------------------------------------------------------------------ #
    # 3. Create new tables                                                #
    # ------------------------------------------------------------------ #

    # municipalities
    op.create_table(
        'municipalities',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # schools
    op.create_table(
        'schools',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('municipality_id', sa.String(64),
                  sa.ForeignKey('municipalities.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('cnpj', sa.String(20), nullable=True),
        sa.Column('institution_type', sa.String(100), nullable=True),
        sa.Column('address_city', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_schools_municipality_id', 'schools', ['municipality_id'])

    # teachers
    op.create_table(
        'teachers',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('school_id', sa.String(64),
                  sa.ForeignKey('schools.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('specialization', sa.String(255), nullable=True),
        sa.Column('email', sa.String(254), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_teachers_school_id', 'teachers', ['school_id'])

    # students
    op.create_table(
        'students',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('school_id', sa.String(64),
                  sa.ForeignKey('schools.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('age', sa.String(10), nullable=True),
        sa.Column('grade', sa.String(50), nullable=True),
        sa.Column('class_name', sa.String(50), nullable=True),
        sa.Column('guardians', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_students_school_id', 'students', ['school_id'])

    # teacher_student_links
    op.create_table(
        'teacher_student_links',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('teacher_id', sa.String(64),
                  sa.ForeignKey('teachers.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('student_id', sa.String(64),
                  sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('teacher_id', 'student_id', name='uq_tsl_teacher_student'),
    )
    op.create_index('idx_tsl_teacher_id', 'teacher_student_links', ['teacher_id'])
    op.create_index('idx_tsl_student_id', 'teacher_student_links', ['student_id'])

    # diary_entries
    op.create_table(
        'diary_entries',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64),
                  sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('diary_date', sa.Date(), nullable=True),
        sa.Column('teacher_attention', sa.String(20), nullable=True),
        sa.Column('followed_agreements', sa.String(20), nullable=True),
        sa.Column('activity_interest', sa.String(20), nullable=True),
        sa.Column('had_lunch', sa.String(20), nullable=True),
        sa.Column('participated_in_play', sa.String(20), nullable=True),
        sa.Column('completed_activities', sa.String(20), nullable=True),
        sa.Column('bathroom_use', sa.String(20), nullable=True),
        sa.Column('open_observation', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('idx_diary_entries_student_id', 'diary_entries', ['student_id'])

    # pdis
    op.create_table(
        'pdis',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('student_id', sa.String(64),
                  sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('birth_date', sa.String(20), nullable=True),
        sa.Column('diagnosis', sa.Text(), nullable=True),
        sa.Column('class_name', sa.String(50), nullable=True),
        sa.Column('guardians', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_pdis_student_id', 'pdis', ['student_id'])

    # pdi_trimester_subjects
    op.create_table(
        'pdi_trimester_subjects',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('pdi_id', sa.String(64),
                  sa.ForeignKey('pdis.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('trimester', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(100), nullable=False),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('adaptations', sa.Text(), nullable=True),
        sa.Column('learnings', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_pdi_trimester_pdi_id', 'pdi_trimester_subjects', ['pdi_id'])

    # user_profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('username', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(64), nullable=False),
        sa.Column('municipality_id', sa.String(64),
                  sa.ForeignKey('municipalities.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('school_id', sa.String(64),
                  sa.ForeignKey('schools.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('teacher_id', sa.String(64),
                  sa.ForeignKey('teachers.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('username', name='uq_user_profiles_username'),
    )
    op.create_index('idx_user_profiles_role', 'user_profiles', ['role'])
    op.create_index('idx_user_profiles_school_id', 'user_profiles', ['school_id'])
    op.create_index('idx_user_profiles_municipality_id', 'user_profiles', ['municipality_id'])

    # chat_sessions
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('session_date', sa.Date(), nullable=True),
        sa.Column('created_by_user_id', sa.String(64),
                  sa.ForeignKey('user_profiles.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('created_by_username', sa.String(120), nullable=False),
        sa.Column('created_by_role', sa.String(64), nullable=False),
        sa.Column('municipality_id', sa.String(64),
                  sa.ForeignKey('municipalities.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('school_id', sa.String(64),
                  sa.ForeignKey('schools.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('teacher_id', sa.String(64),
                  sa.ForeignKey('teachers.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('student_id', sa.String(64),
                  sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('student_name', sa.String(255), nullable=True),
        sa.Column('school_name', sa.String(255), nullable=True),
        sa.Column('extra', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_chat_sessions_day', 'chat_sessions', ['session_date'])
    op.create_index('idx_chat_sessions_municipality', 'chat_sessions', ['municipality_id'])
    op.create_index('idx_chat_sessions_school', 'chat_sessions', ['school_id'])
    op.create_index('idx_chat_sessions_student', 'chat_sessions', ['student_id'])

    # chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('session_id', sa.String(64),
                  sa.ForeignKey('chat_sessions.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('message_index', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(64),
                  sa.ForeignKey('user_profiles.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
        sa.Column('username', sa.String(120), nullable=True),
        sa.Column('sources', JSON, nullable=True),
        sa.Column('extra', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_chat_messages_session', 'chat_messages', ['session_id'])

    # case_study_submissions
    op.create_table(
        'case_study_submissions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('answers', JSON, nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
    )

    # school_registration_submissions
    op.create_table(
        'school_registration_submissions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('answers', JSON, nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
    )

    # object_storage_files
    op.create_table(
        'object_storage_files',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('doc_type', sa.String(64), nullable=False),
        sa.Column('reference_id', sa.String(128), nullable=False),
        sa.Column('bucket', sa.String(128), nullable=False),
        sa.Column('object_key', sa.String(512), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(120), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('extra', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('doc_type', 'reference_id', name='uq_object_storage_doc_ref'),
    )

    # diary_embedding_gemini
    op.execute("""
        CREATE TABLE diary_embedding_gemini (
            id SERIAL PRIMARY KEY,
            diary_entry_id VARCHAR(64) REFERENCES diary_entries(id) ON UPDATE CASCADE ON DELETE CASCADE,
            student_id VARCHAR(64) REFERENCES students(id) ON UPDATE CASCADE ON DELETE CASCADE,
            content TEXT,
            meta_data JSON,
            embedding vector(768),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index('idx_diary_emb_diary_entry_id', 'diary_embedding_gemini', ['diary_entry_id'])
    op.create_index('idx_diary_emb_student_id', 'diary_embedding_gemini', ['student_id'])

    # pdi_embedding_gemini
    op.execute("""
        CREATE TABLE pdi_embedding_gemini (
            id SERIAL PRIMARY KEY,
            pdi_id VARCHAR(64) NOT NULL REFERENCES pdis(id) ON UPDATE CASCADE ON DELETE CASCADE,
            student_id VARCHAR(64) NOT NULL REFERENCES students(id) ON UPDATE CASCADE ON DELETE CASCADE,
            content TEXT NOT NULL,
            meta_data JSON,
            embedding vector(768),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index('idx_pdi_emb_pdi_id', 'pdi_embedding_gemini', ['pdi_id'])
    op.create_index('idx_pdi_emb_student_id', 'pdi_embedding_gemini', ['student_id'])


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pdi_embedding_gemini CASCADE")
    op.execute("DROP TABLE IF EXISTS diary_embedding_gemini CASCADE")
    op.execute("DROP TABLE IF EXISTS object_storage_files CASCADE")
    op.execute("DROP TABLE IF EXISTS school_registration_submissions CASCADE")
    op.execute("DROP TABLE IF EXISTS case_study_submissions CASCADE")
    op.execute("DROP TABLE IF EXISTS chat_messages CASCADE")
    op.execute("DROP TABLE IF EXISTS chat_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS user_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS pdi_trimester_subjects CASCADE")
    op.execute("DROP TABLE IF EXISTS pdis CASCADE")
    op.execute("DROP TABLE IF EXISTS diary_entries CASCADE")
    op.execute("DROP TABLE IF EXISTS teacher_student_links CASCADE")
    op.execute("DROP TABLE IF EXISTS students CASCADE")
    op.execute("DROP TABLE IF EXISTS teachers CASCADE")
    op.execute("DROP TABLE IF EXISTS schools CASCADE")
    op.execute("DROP TABLE IF EXISTS municipalities CASCADE")
