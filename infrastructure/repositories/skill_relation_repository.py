"""Relações entre habilidades do aluno (habilidade → outra habilidade ou campo de experiência)."""
import json
import uuid
from typing import Optional
from sqlalchemy import select, func

from core.constants.bncc_fields import EXPERIENCE_FIELDS
from core.interfaces.i_skill_relation_repository import ISkillRelationRepository, SkillRelationError
from infrastructure.database_context.database import Database
from infrastructure.models.bncc import BnccSkill, StudentSkillScore
from infrastructure.models.skill_relation import StudentSkillRelation, KIND_SKILL, KIND_FIELD
from infrastructure.models.student import Student


def _actions(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        v = json.loads(raw)
    except Exception:
        return []
    return [str(a).strip() for a in v if str(a).strip()] if isinstance(v, list) else []


def _skill_brief(s: BnccSkill, score: int = 0) -> dict:
    return {"id": s.id, "code": s.code, "grade": s.grade, "area": s.area, "description": s.description, "score": score}


def _dump_actions(value) -> Optional[str]:
    items = [str(a).strip() for a in (value or []) if str(a).strip()]
    return json.dumps(items, ensure_ascii=False) if items else None


class SkillRelationRepository(ISkillRelationRepository):
    def __init__(self, database: Database) -> None:
        self.database = database

    async def overview(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            counts = dict((await session.execute(
                select(StudentSkillRelation.skill_id, func.count())
                .where(StudentSkillRelation.student_id == student_id, StudentSkillRelation.deleted == False)  # noqa: E712
                .group_by(StudentSkillRelation.skill_id)
            )).all())
            rows = (await session.execute(
                select(StudentSkillScore, BnccSkill).join(BnccSkill, BnccSkill.id == StudentSkillScore.skill_id)
                .where(StudentSkillScore.student_id == student_id, BnccSkill.deleted == False,  # noqa: E712
                       (StudentSkillScore.score > 0) | (StudentSkillScore.indirect_only == True)  # noqa: E712
                       | StudentSkillScore.skill_id.in_(list(counts) or [""]))
                .order_by(BnccSkill.grade_order, BnccSkill.code)
            )).all()
            return [{**_skill_brief(sk, sc.score or 0), "indirect_only": bool(sc.indirect_only),
                     "relations": counts.get(sk.id, 0)} for sc, sk in rows]

    async def list_relations(self, student_id: str, skill_id: str) -> list[dict]:
        async with self.database.session() as session:
            rels = (await session.execute(
                select(StudentSkillRelation).where(
                    StudentSkillRelation.student_id == student_id, StudentSkillRelation.skill_id == skill_id,
                    StudentSkillRelation.deleted == False)  # noqa: E712
                .order_by(StudentSkillRelation.created_at)
            )).scalars().all()
            ids = [r.related_skill_id for r in rels if r.related_skill_id]
            skills = {s.id: s for s in (await session.execute(select(BnccSkill).where(BnccSkill.id.in_(ids or [""])))).scalars().all()}
            scores = {sc.skill_id: sc.score or 0 for sc in (await session.execute(
                select(StudentSkillScore).where(StudentSkillScore.student_id == student_id,
                                                StudentSkillScore.skill_id.in_(ids or [""])))).scalars().all()}
            return [self._dict(r, skills.get(r.related_skill_id), scores.get(r.related_skill_id, 0)) for r in rels]

    @staticmethod
    def _dict(r: StudentSkillRelation, related: Optional[BnccSkill], score: int) -> dict:
        return {
            "id": r.id, "skill_id": r.skill_id, "kind": r.kind, "field_key": r.field_key,
            "related_skill": _skill_brief(related, score) if related else None,
            "adaptation": r.adaptation or "", "justification": r.justification or "", "actions": _actions(r.actions),
            "source": r.source, "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

    async def skill_info(self, student_id: str, skill_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            skill = await session.get(BnccSkill, skill_id)
            if not skill or skill.deleted:
                return None
            sc = await session.get(StudentSkillScore, (student_id, skill_id))
            return {**_skill_brief(skill, sc.score if sc else 0), "indirect_only": bool(sc.indirect_only) if sc else False}

    async def resolve_codes(self, codes: list[str]) -> dict[str, dict]:
        if not codes:
            return {}
        async with self.database.session() as session:
            rows = (await session.execute(
                select(BnccSkill).where(BnccSkill.code.in_(codes), BnccSkill.deleted == False))).scalars().all()  # noqa: E712
            return {s.code: _skill_brief(s) for s in rows}

    async def create(self, student_id: str, skill_id: str, data: dict, user: dict, source: str) -> dict:
        kind = data.get("kind")
        related_id, field_key = data.get("related_skill_id"), data.get("field_key")
        async with self.database.session() as session:
            if not await session.get(Student, student_id):
                raise SkillRelationError("Aluno não encontrado.")
            skill = await session.get(BnccSkill, skill_id)
            if not skill or skill.deleted:
                raise SkillRelationError("Habilidade não encontrada.")
            related = None
            if kind == KIND_SKILL:
                if not related_id or related_id == skill_id:
                    raise SkillRelationError("Escolha outra habilidade para relacionar.")
                related = await session.get(BnccSkill, related_id)
                if not related or related.deleted:
                    raise SkillRelationError("Habilidade relacionada não encontrada.")
                field_key = None
            elif kind == KIND_FIELD:
                if field_key not in EXPERIENCE_FIELDS:
                    raise SkillRelationError("Campo de experiência inválido.")
                related_id = None
            else:
                raise SkillRelationError("Tipo de relação inválido.")
            same = (await session.execute(select(StudentSkillRelation).where(
                StudentSkillRelation.student_id == student_id, StudentSkillRelation.skill_id == skill_id,
                StudentSkillRelation.kind == kind, StudentSkillRelation.related_skill_id.is_(related_id) if related_id is None
                else StudentSkillRelation.related_skill_id == related_id,
                StudentSkillRelation.field_key.is_(field_key) if field_key is None else StudentSkillRelation.field_key == field_key,
                StudentSkillRelation.deleted == False))).scalars().first()  # noqa: E712
            if same:
                raise SkillRelationError("Essa relação já existe.")
            row = StudentSkillRelation(
                id=str(uuid.uuid4()), student_id=student_id, skill_id=skill_id, kind=kind, related_skill_id=related_id,
                field_key=field_key, adaptation=(data.get("adaptation") or "").strip() or None,
                justification=(data.get("justification") or "").strip() or None,
                actions=_dump_actions(data.get("actions")), source=source, created_by=user.get("username"),
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            score = 0
            if related:
                sc = await session.get(StudentSkillScore, (student_id, related.id))
                score = sc.score if sc else 0
            return self._dict(row, related, score)

    async def update(self, student_id: str, relation_id: str, data: dict) -> dict:
        async with self.database.session() as session:
            row = await session.get(StudentSkillRelation, relation_id)
            if not row or row.deleted or row.student_id != student_id:
                raise SkillRelationError("Relação não encontrada.")
            if "adaptation" in data:
                row.adaptation = (data["adaptation"] or "").strip() or None
            if "justification" in data:
                row.justification = (data["justification"] or "").strip() or None
            if "actions" in data:
                row.actions = _dump_actions(data["actions"])
            row.source = "manual"  # editada por uma pessoa
            await session.commit()
            await session.refresh(row)
            related = await session.get(BnccSkill, row.related_skill_id) if row.related_skill_id else None
            sc = await session.get(StudentSkillScore, (student_id, row.related_skill_id)) if related else None
            return self._dict(row, related, sc.score if sc else 0)

    async def delete(self, student_id: str, relation_id: str) -> bool:
        async with self.database.session() as session:
            row = await session.get(StudentSkillRelation, relation_id)
            if not row or row.deleted or row.student_id != student_id:
                return False
            row.deleted = True
            await session.commit()
            return True
