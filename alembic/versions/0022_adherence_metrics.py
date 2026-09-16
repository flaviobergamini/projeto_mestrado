"""add fields for adherence/engagement metrics (support level, teacher demographics, parent demographics)

Revision ID: 0022_add_adherence_metrics_fields
Revises: 0021_create_diary_summaries
Create Date: 2026-09-08
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0022_adherence_metrics'
down_revision: Union[str, Sequence[str], None] = '0021_create_diary_summaries'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # students — nível de suporte do autismo (DSM-5)
    op.add_column('students', sa.Column('autism_support_level', sa.String(10), nullable=True))
    op.create_check_constraint(
        'ck_students_autism_support_level',
        'students',
        "autism_support_level IN ('1', '2', '3')",
    )

    # teachers — composição do corpo docente
    op.add_column('teachers', sa.Column('birth_year', sa.Integer(), nullable=True))
    op.add_column('teachers', sa.Column('gender', sa.String(20), nullable=True))
    op.add_column('teachers', sa.Column('teacher_role', sa.String(30), nullable=True))
    op.create_check_constraint(
        'ck_teachers_gender',
        'teachers',
        "gender IN ('feminino', 'masculino', 'outro', 'nao_informado')",
    )
    op.create_check_constraint(
        'ck_teachers_teacher_role',
        'teachers',
        "teacher_role IN ('regente', 'apoio', 'aee', 'coordenacao_pedagogica', 'outro')",
    )

    # user_profiles — demografia do responsável (role="parent")
    op.add_column('user_profiles', sa.Column('birth_year', sa.Integer(), nullable=True))
    op.add_column('user_profiles', sa.Column('income_bracket', sa.String(30), nullable=True))
    op.add_column('user_profiles', sa.Column('single_parent', sa.Boolean(), nullable=True))
    op.add_column('user_profiles', sa.Column('children_count', sa.Integer(), nullable=True))
    op.add_column('user_profiles', sa.Column('neurodivergent_children_count', sa.Integer(), nullable=True))
    op.create_check_constraint(
        'ck_user_profiles_income_bracket',
        'user_profiles',
        "income_bracket IN ('ate_1_sm', '1_a_3_sm', '3_a_5_sm', '5_a_10_sm', 'acima_10_sm', 'nao_informado')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_user_profiles_income_bracket', 'user_profiles', type_='check')
    op.drop_column('user_profiles', 'neurodivergent_children_count')
    op.drop_column('user_profiles', 'children_count')
    op.drop_column('user_profiles', 'single_parent')
    op.drop_column('user_profiles', 'income_bracket')
    op.drop_column('user_profiles', 'birth_year')

    op.drop_constraint('ck_teachers_teacher_role', 'teachers', type_='check')
    op.drop_constraint('ck_teachers_gender', 'teachers', type_='check')
    op.drop_column('teachers', 'teacher_role')
    op.drop_column('teachers', 'gender')
    op.drop_column('teachers', 'birth_year')

    op.drop_constraint('ck_students_autism_support_level', 'students', type_='check')
    op.drop_column('students', 'autism_support_level')
