"""recupera no JSON do grafo TODAS as relações antigas (habilidades e campos de experiência, com adaptação e ações)

A 0051 só copiou relações habilidade↔habilidade. Aqui o documento JSON de cada (aluno, finalística) passa a conter também
os campos de experiência e os textos antigos, e cada habilidade que tinha relações volta a ser marcada como finalística.
Idempotente: o que já está no JSON não é duplicado. A tabela antiga continua intacta.

Revision ID: 0052_skill_graphs_backfill
Revises: 0051_skill_graphs
Create Date: 2026-11-23
"""
import json
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0052_skill_graphs_backfill'
down_revision: Union[str, Sequence[str], None] = '0051_skill_graphs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _dec(decrypt, value):
    if not value:
        return ""
    try:
        return decrypt(value)
    except Exception:
        return ""


def upgrade() -> None:
    from infrastructure.utils.encryption import encrypt, decrypt
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id, student_id, skill_id, kind, related_skill_id, field_key, adaptation, justification, actions, source "
        "FROM student_skill_relations WHERE deleted = false ORDER BY created_at")).fetchall()
    existing = {(r[0], r[1]): (r[2], r[3]) for r in bind.execute(sa.text(
        "SELECT student_id, skill_id, document, revision FROM student_skill_graphs")).fetchall()}
    docs: dict[tuple[str, str], dict] = {}
    for key, (raw, _rev) in existing.items():
        try:
            docs[key] = json.loads(decrypt(raw))
        except Exception:
            docs[key] = {"schema": 1, "related": []}
    touched: set[tuple[str, str]] = set()
    for rid, student_id, skill_id, kind, related_id, field_key, adaptation, justification, actions, source in rows:
        doc = docs.setdefault((student_id, skill_id), {"schema": 1, "related": []})
        if kind == "field":
            if not field_key or any(r.get("kind") == "field" and r.get("field_key") == field_key for r in doc["related"]):
                continue
            node = {"kind": "field", "field_key": field_key}
        else:
            if not related_id or any(r.get("skill_id") == related_id for r in doc["related"]):
                continue
            node = {"kind": "skill", "skill_id": related_id}
        try:
            acts = json.loads(_dec(decrypt, actions) or "[]")
        except Exception:
            acts = []
        doc["related"].append({"id": rid, **node, "direction": "out", "origin": source or "manual",
                               "reason": _dec(decrypt, justification), "adaptation": _dec(decrypt, adaptation),
                               "actions": acts if isinstance(acts, list) else [], "x": None, "y": None})
        touched.add((student_id, skill_id))
    for (student_id, skill_id) in touched:
        payload = {"s": student_id, "k": skill_id, "d": encrypt(json.dumps(docs[(student_id, skill_id)], ensure_ascii=False))}
        if (student_id, skill_id) in existing:
            bind.execute(sa.text("UPDATE student_skill_graphs SET document = :d, revision = revision + 1, updated_by = 'migration', "
                                 "updated_at = now() WHERE student_id = :s AND skill_id = :k"), payload)
        else:
            bind.execute(sa.text("INSERT INTO student_skill_graphs (student_id, skill_id, document, revision, updated_by) "
                                 "VALUES (:s, :k, :d, 1, 'migration')"), payload)
    for (student_id, skill_id), doc in docs.items():  # quem tem relações é finalística
        if doc["related"]:
            bind.execute(sa.text("UPDATE student_skill_scores SET finalistic = true WHERE student_id = :s AND skill_id = :k"),
                         {"s": student_id, "k": skill_id})


def downgrade() -> None:
    pass  # dados só acrescentados; nada a desfazer
