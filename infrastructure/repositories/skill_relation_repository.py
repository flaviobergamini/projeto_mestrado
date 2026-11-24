"""Grafo de relações do aluno: um documento JSON por habilidade finalística (tabela student_skill_graphs)."""
import json
from typing import Callable, Optional
from sqlalchemy import select

from core.interfaces.i_skill_relation_repository import ISkillRelationRepository, SkillRelationError  # noqa: F401
from infrastructure.database_context.database import Database
from infrastructure.models.bncc import BnccSkill, StudentSkillScore
from infrastructure.models.skill_relation import StudentSkillGraph


def _empty() -> dict:
    return {"schema": 1, "related": []}


def _load(raw: Optional[str]) -> dict:
    try:
        doc = json.loads(raw) if raw else _empty()
    except Exception:
        doc = _empty()
    if not isinstance(doc, dict) or not isinstance(doc.get("related"), list):
        doc = _empty()
    return doc


def _brief(s: BnccSkill, score: int, observation: str = "") -> dict:
    return {"id": s.id, "code": s.code, "grade": s.grade, "area": s.area, "description": s.description,
            "score": score, "observation": observation}


class SkillRelationRepository(ISkillRelationRepository):
    def __init__(self, database: Database) -> None:
        self.database = database

    async def overview(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            rows = (await session.execute(
                select(StudentSkillScore, BnccSkill).join(BnccSkill, BnccSkill.id == StudentSkillScore.skill_id)
                .where(StudentSkillScore.student_id == student_id, BnccSkill.deleted == False,  # noqa: E712
                       StudentSkillScore.score >= 1, StudentSkillScore.score <= 4)  # 0 e 5 estrelas não aparecem
                .order_by(BnccSkill.grade_order, BnccSkill.code)
            )).all()
            graphs = (await session.execute(select(StudentSkillGraph).where(StudentSkillGraph.student_id == student_id))).scalars().all()
            counts = {g.skill_id: len(_load(g.document)["related"]) for g in graphs}
            return [{**{k: v for k, v in _brief(sk, sc.score or 0).items() if k != "observation"},
                     "finalistic": bool(sc.finalistic), "relations": counts.get(sk.id, 0),
                     "updated_at": sc.updated_at.isoformat() if sc.updated_at else None} for sc, sk in rows]

    async def get_document(self, student_id: str, skill_id: str) -> tuple[dict, int]:
        async with self.database.session() as session:
            row = await session.get(StudentSkillGraph, (student_id, skill_id))
            return (_load(row.document), row.revision) if row else (_empty(), 0)

    async def mutate(self, student_id: str, skill_id: str, change: Callable[[dict], None], user: dict) -> tuple[dict, int]:
        async with self.database.session() as session:
            row = (await session.execute(
                select(StudentSkillGraph).where(StudentSkillGraph.student_id == student_id, StudentSkillGraph.skill_id == skill_id)
                .with_for_update())).scalars().first()
            doc = _load(row.document) if row else _empty()
            change(doc)  # pode abortar com SkillRelationError
            payload = json.dumps(doc, ensure_ascii=False)
            if row:
                row.document, row.revision, row.updated_by = payload, (row.revision or 0) + 1, user.get("username")
            else:
                row = StudentSkillGraph(student_id=student_id, skill_id=skill_id, document=payload, revision=1,
                                        updated_by=user.get("username"))
                session.add(row)
            await session.commit()
            return doc, row.revision

    async def find_skill_of_relation(self, student_id: str, relation_id: str) -> Optional[str]:
        async with self.database.session() as session:
            graphs = (await session.execute(select(StudentSkillGraph).where(StudentSkillGraph.student_id == student_id))).scalars().all()
            for g in graphs:
                if any(r.get("id") == relation_id for r in _load(g.document)["related"]):
                    return g.skill_id
            return None

    async def skill_info(self, student_id: str, skill_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            skill = await session.get(BnccSkill, skill_id)
            if not skill or skill.deleted:
                return None
            sc = await session.get(StudentSkillScore, (student_id, skill_id))
            return {**_brief(skill, sc.score if sc else 0, (sc.observation or "") if sc else ""),
                    "finalistic": bool(sc.finalistic) if sc else False}

    async def skill_briefs(self, student_id: str, skill_ids: list[str]) -> dict[str, dict]:
        if not skill_ids:
            return {}
        async with self.database.session() as session:
            skills = {s.id: s for s in (await session.execute(
                select(BnccSkill).where(BnccSkill.id.in_(skill_ids), BnccSkill.deleted == False))).scalars().all()}  # noqa: E712
            scores = {sc.skill_id: sc for sc in (await session.execute(select(StudentSkillScore).where(
                StudentSkillScore.student_id == student_id, StudentSkillScore.skill_id.in_(skill_ids)))).scalars().all()}
            return {i: _brief(s, (scores[i].score or 0) if i in scores else 0, (scores[i].observation or "") if i in scores else "")
                    for i, s in skills.items()}

    async def candidates(self, student_id: str, exclude_skill_id: str) -> list[dict]:
        async with self.database.session() as session:
            rows = (await session.execute(
                select(StudentSkillScore, BnccSkill).join(BnccSkill, BnccSkill.id == StudentSkillScore.skill_id)
                .where(StudentSkillScore.student_id == student_id, BnccSkill.deleted == False,  # noqa: E712
                       StudentSkillScore.score >= 1, StudentSkillScore.score <= 4, BnccSkill.id != exclude_skill_id)
                .order_by(BnccSkill.grade_order, BnccSkill.code)
            )).all()
            return [_brief(sk, sc.score or 0, sc.observation or "") for sc, sk in rows]
