"""apaga dos grafos as ligações antigas com campos de experiência (nós "field", sem código de habilidade)

O grafo passa a ter só habilidades. A tabela antiga student_skill_relations continua intacta como cópia de segurança.

Revision ID: 0054_skill_graphs_drop_fields
Revises: 0053_skill_graphs_no_arrows
Create Date: 2026-11-25
"""
import json
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0054_skill_graphs_drop_fields'
down_revision: Union[str, Sequence[str], None] = '0053_skill_graphs_no_arrows'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from infrastructure.utils.encryption import encrypt, decrypt
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT student_id, skill_id, document FROM student_skill_graphs")).fetchall()
    removed = graphs = 0
    for student_id, skill_id, raw in rows:
        doc = json.loads(decrypt(raw))
        related = doc.get("related") or []
        kept = [r for r in related if r.get("kind") != "field"]
        if len(kept) == len(related):
            continue
        removed, graphs = removed + len(related) - len(kept), graphs + 1
        doc["related"] = kept
        bind.execute(sa.text("UPDATE student_skill_graphs SET document = :d, revision = revision + 1, updated_by = 'migration', "
                             "updated_at = now() WHERE student_id = :s AND skill_id = :k"),
                     {"d": encrypt(json.dumps(doc, ensure_ascii=False)), "s": student_id, "k": skill_id})
    print(f"0054: {removed} ligação(ões) com campo de experiência apagada(s) em {graphs} grafo(s).")


def downgrade() -> None:
    pass  # não restaura; os originais estão em student_skill_relations
