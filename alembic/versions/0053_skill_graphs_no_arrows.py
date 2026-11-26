"""relações dos grafos passam a ser bidirecionais (sem seta)

Revision ID: 0053_skill_graphs_no_arrows
Revises: 0052_skill_graphs_backfill
Create Date: 2026-11-25
"""
import json
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0053_skill_graphs_no_arrows'
down_revision: Union[str, Sequence[str], None] = '0052_skill_graphs_backfill'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from infrastructure.utils.encryption import encrypt, decrypt
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT student_id, skill_id, document FROM student_skill_graphs")).fetchall()
    for student_id, skill_id, raw in rows:
        doc = json.loads(decrypt(raw))
        changed = False
        for r in doc.get("related") or []:
            if r.get("direction") != "both":
                r["direction"], changed = "both", True
        if changed:
            bind.execute(sa.text("UPDATE student_skill_graphs SET document = :d, revision = revision + 1, updated_at = now() "
                                 "WHERE student_id = :s AND skill_id = :k"),
                         {"d": encrypt(json.dumps(doc, ensure_ascii=False)), "s": student_id, "k": skill_id})


def downgrade() -> None:
    pass  # a direção anterior não é restaurada
