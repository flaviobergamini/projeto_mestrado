import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository
from infrastructure.database_context.database import Database
from infrastructure.models.bncc import (
    BnccSkill, StudentSkillScore, StudentSkillEvent, SkillSuggestion,
)
from infrastructure.models.pei_kanban_card import PeiKanbanCard


def _codes(raw: Optional[str]) -> list[str]:
    try:
        v = json.loads(raw) if raw else []
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


class SkillPlanRepository(ISkillPlanRepository):
    """Plano por habilidade: alvos das rodadas da IA, gravação dos rascunhos e sugestões de nota."""

    def __init__(self, database: Database) -> None:
        self.database = database

    async def plan_skills(self, student_id: str) -> list[dict]:
        """Habilidades no PDI do aluno que a IA PODE trabalhar (não marcadas como 'sem IA')."""
        async with self.database.session() as session:
            rows = await session.execute(
                select(StudentSkillScore, BnccSkill)
                .join(BnccSkill, BnccSkill.id == StudentSkillScore.skill_id)
                .where(
                    StudentSkillScore.student_id == student_id, StudentSkillScore.in_plan == True,  # noqa: E712
                    StudentSkillScore.ai_excluded == False, BnccSkill.deleted == False,  # noqa: E712
                )
                .order_by(BnccSkill.grade_order, BnccSkill.code)
            )
            return [{
                "skill_id": sk.id, "code": sk.code, "grade": sk.grade, "area": sk.area,
                "description": sk.description, "score": sc.score,
                "adaptation": sc.adaptation or "", "justification": sc.justification or "",
                "actions": sc.actions or "", "correlated_codes": _codes(sc.correlated_codes),
            } for sc, sk in rows.all()]

    async def apply_round1(self, student_id: str, drafts: dict[str, dict], user: dict) -> list[str]:
        """Grava rascunhos da IA SOMENTE em campos vazios (nunca sobrescreve texto humano).

        `drafts` é indexado por skill_id. Retorna os skill_ids realmente alterados."""
        changed: list[str] = []
        async with self.database.session() as session:
            for skill_id, d in drafts.items():
                row = await session.get(StudentSkillScore, (student_id, skill_id))
                if not row or row.ai_excluded or not row.in_plan:
                    continue
                touched = False
                for field in ("adaptation", "justification", "actions"):
                    if not (getattr(row, field) or "").strip() and (d.get(field) or "").strip():
                        setattr(row, field, d[field].strip())
                        touched = True
                if not _codes(row.correlated_codes) and d.get("correlated_codes"):
                    row.correlated_codes = json.dumps(d["correlated_codes"], ensure_ascii=False)
                    touched = True
                if touched:
                    row.plan_ai_at = datetime.utcnow()
                    session.add(StudentSkillEvent(
                        id=str(uuid.uuid4()), student_id=student_id, skill_id=skill_id, kind="ai_plan",
                        old_score=row.score, new_score=row.score,
                        note="Rascunho do quadro gerado pela IA (revisar).",
                        user_id=user.get("user_id"), username=user.get("username"),
                    ))
                    changed.append(skill_id)
            await session.commit()
        return changed

    async def cards_by_skill(self, student_id: str, skill_ids: list[str]) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {s: [] for s in skill_ids}
        if not skill_ids:
            return out
        async with self.database.session() as session:
            rows = await session.execute(
                select(PeiKanbanCard).where(
                    PeiKanbanCard.student_id == student_id, PeiKanbanCard.skill_id.in_(skill_ids),
                    PeiKanbanCard.deleted == False,  # noqa: E712
                ).order_by(PeiKanbanCard.created_at)
            )
            for c in rows.scalars().all():
                out[c.skill_id].append({
                    "id": c.id, "title": c.title, "status": c.status, "daily_log": c.daily_log or "",
                    "reaction": c.reaction, "score_at_creation": c.score_at_creation,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                })
        return out

    async def replace_pending_suggestions(self, student_id: str, items: list[dict]) -> list[dict]:
        """Descarta sugestões pendentes antigas do aluno e grava as novas."""
        async with self.database.session() as session:
            old = await session.execute(
                select(SkillSuggestion).where(SkillSuggestion.student_id == student_id, SkillSuggestion.status == "pending")
            )
            for s in old.scalars().all():
                await session.delete(s)
            created = []
            for it in items:
                s = SkillSuggestion(
                    id=str(uuid.uuid4()), student_id=student_id, skill_id=it["skill_id"],
                    current_score=it["current_score"], suggested_score=it["suggested_score"],
                    reason=it.get("reason"), evidence_card_ids=json.dumps(it.get("evidence_card_ids") or []),
                )
                session.add(s)
                created.append(s)
            await session.commit()
        return await self.list_suggestions(student_id)

    async def list_suggestions(self, student_id: str, status: str = "pending") -> list[dict]:
        async with self.database.session() as session:
            rows = await session.execute(
                select(SkillSuggestion, BnccSkill).join(BnccSkill, BnccSkill.id == SkillSuggestion.skill_id)
                .where(SkillSuggestion.student_id == student_id, SkillSuggestion.status == status)
                .order_by(SkillSuggestion.created_at.desc())
            )
            return [{
                "id": s.id, "skill_id": s.skill_id, "code": sk.code, "description": sk.description,
                "current_score": s.current_score, "suggested_score": s.suggested_score, "reason": s.reason,
                "evidence_card_ids": _codes(s.evidence_card_ids), "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            } for s, sk in rows.all()]

    async def decide(self, suggestion_id: str, accept: bool, user: dict) -> Optional[dict]:
        """A professora decide: aceitar aplica a nova nota (com histórico); recusar só registra."""
        async with self.database.session() as session:
            s = await session.get(SkillSuggestion, suggestion_id)
            if not s or s.status != "pending":
                return None
            s.status = "accepted" if accept else "rejected"
            s.decided_by = user.get("username")
            s.decided_at = datetime.utcnow()
            if accept:
                row = await session.get(StudentSkillScore, (s.student_id, s.skill_id))
                if not row:
                    row = StudentSkillScore(student_id=s.student_id, skill_id=s.skill_id, score=0, ai_excluded=False, in_plan=False)
                    session.add(row)
                old = row.score or 0
                row.score = s.suggested_score
                row.updated_by_user_id = user.get("user_id")
                row.updated_by_username = user.get("username")
                if old != row.score:
                    session.add(StudentSkillEvent(
                        id=str(uuid.uuid4()), student_id=s.student_id, skill_id=s.skill_id, kind="ai_suggestion",
                        old_score=old, new_score=row.score, note=s.reason, evidence_card_ids=s.evidence_card_ids,
                        user_id=user.get("user_id"), username=user.get("username"),
                    ))
            await session.commit()
            return {"id": s.id, "status": s.status}
