"""grafo de relações como documento JSON (student_skill_graphs); migra as relações existentes

Cada habilidade finalística de um aluno passa a ter UM documento JSON com os nós relacionados. As relações antigas
(tabela student_skill_relations) são copiadas para o JSON (só as que ligam habilidades; o motivo vem da justificativa).
A tabela antiga NÃO é apagada: fica como cópia de segurança, sem novas gravações.

Revision ID: 0051_skill_graphs
Revises: 0050_skill_finalistic
Create Date: 2026-11-23
"""
import json
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0051_skill_graphs'
down_revision: Union[str, Sequence[str], None] = '0050_skill_finalistic'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from infrastructure.utils.encryption import encrypt, decrypt
    op.create_table(
        'student_skill_graphs',
        sa.Column('student_id', sa.String(64), sa.ForeignKey('students.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('skill_id', sa.String(64), sa.ForeignKey('bncc_skills.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
        sa.Column('document', sa.Text(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_by', sa.String(120), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id, student_id, skill_id, related_skill_id, justification, source, created_by FROM student_skill_relations "
        "WHERE deleted = false AND kind = 'skill' AND related_skill_id IS NOT NULL ORDER BY created_at")).fetchall()
    docs: dict[tuple[str, str], dict] = {}
    for rid, student_id, skill_id, related_id, justification, source, created_by in rows:
        doc = docs.setdefault((student_id, skill_id), {"schema": 1, "related": []})
        reason = ""
        if justification:
            try:
                reason = decrypt(justification)
            except Exception:
                reason = ""
        doc["related"].append({"id": rid, "skill_id": related_id, "direction": "out", "origin": source or "manual",
                               "reason": reason, "x": None, "y": None})
    for (student_id, skill_id), doc in docs.items():
        bind.execute(sa.text(
            "INSERT INTO student_skill_graphs (student_id, skill_id, document, revision, updated_by) "
            "VALUES (:s, :k, :d, 1, 'migration')"), {"s": student_id, "k": skill_id, "d": encrypt(json.dumps(doc, ensure_ascii=False))})


def downgrade() -> None:
    op.drop_table('student_skill_graphs')
