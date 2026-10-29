import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func, or_, and_
from core.interfaces.i_bncc_repository import IBnccRepository, BnccError
from core.services.skill_actions import (
    normalize_adaptations, dump_adaptations, merge_adaptations, actor_from_user, owns, is_coordinator,
)
from infrastructure.repositories.responsibles import default_responsible, fill_responsibles
from infrastructure.database_context.database import Database
from infrastructure.models.bncc import BnccSkill, StudentSkillScore, SkillReport, StudentSkillEvent
from infrastructure.models.student import Student


def _skill_dict(s: BnccSkill) -> dict:
    return {
        "id": s.id, "stage": s.stage, "grade": s.grade, "grade_order": s.grade_order,
        "grade_from": s.grade_from, "grade_to": s.grade_to, "area": s.area, "code": s.code, "description": s.description, "position": s.position,
    }


def _load_codes(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


# Com 5 estrelas a habilidade fica travada; só estes perfis ainda conseguem corrigir (ex.: nota marcada por engano).
LOCK_OVERRIDE_ROLES = ("admin", "coordenacao")


def _plan_dict(row: Optional[StudentSkillScore], actor: Optional[dict] = None) -> dict:
    return {
        "summary": (row.summary or "") if row else "",
        "adaptation": (row.adaptation or "") if row else "",
        "justification": (row.justification or "") if row else "",
        # `editable`: o usuário logado é o responsável (ou da coordenação) e pode alterar esta adaptação
        "adaptations": [
            {**g, "editable": owns(g.get("responsible"), actor) if actor else True}
            for g in (normalize_adaptations(row.actions) if row else [])
        ],
        "can_assign_responsible": is_coordinator(actor) if actor else False,
        "experience_fields": _load_codes(row.correlated_codes) if row else [],
        "ai_excluded": bool(row.ai_excluded) if row else False,
        "in_plan": bool(row.in_plan) if row else False,
        "plan_ai_at": row.plan_ai_at.isoformat() if row and row.plan_ai_at else None,
    }


INFANTIL_LABEL = "Infantil (4 anos a 5 anos e 11 meses)"


def _grade_number(label: str) -> Optional[int]:
    """Número do ano a partir do rótulo ('3º ano' -> 3; Infantil -> 0)."""
    if label.strip().lower().startswith("infantil"):
        return 0
    m = re.match(r"\s*(\d+)", label)
    return int(m.group(1)) if m else None


def _grade_label(stage: str, y_from: int, y_to: int, infantil_label: str = INFANTIL_LABEL) -> str:
    if stage == "infantil":
        return infantil_label
    return f"{y_from}º ano" if y_from == y_to else f"{y_from}º ao {y_to}º ano"


class BnccRepository(IBnccRepository):
    def __init__(self, database: Database) -> None:
        self.database = database

    # ── catálogo ──────────────────────────────────────────────────────────────

    async def list_grades(self) -> list[dict]:
        """Um item por ano; `count` = habilidades que cobrem aquele ano (a mesma habilidade conta em vários anos)."""
        async with self.database.session() as session:
            rows = (await session.execute(
                select(BnccSkill.stage, BnccSkill.grade, BnccSkill.grade_from, BnccSkill.grade_to).where(BnccSkill.deleted == False)
            )).all()
        infantil = next((g for st, g, _, _ in rows if st == "infantil"), INFANTIL_LABEL)
        years = sorted({y for _, _, f, t in rows for y in range(f, t + 1)})
        return [
            {"grade": infantil if y == 0 else f"{y}º ano", "grade_order": y, "stage": "infantil" if y == 0 else "fundamental",
             "count": sum(1 for _, _, f, t in rows if f <= y <= t)}
            for y in years
        ]

    async def list_codes(self) -> list[str]:
        async with self.database.session() as session:
            rows = await session.execute(select(BnccSkill.code).where(BnccSkill.deleted == False).distinct())
            return [r[0] for r in rows.all()]

    async def list_areas(self) -> list[str]:
        async with self.database.session() as session:
            rows = await session.execute(
                select(BnccSkill.area).where(BnccSkill.deleted == False).distinct().order_by(BnccSkill.area)
            )
            return [r[0] for r in rows.all()]

    async def list_skills(
        self, grades: Optional[list[str]] = None, areas: Optional[list[str]] = None, q: Optional[str] = None,
    ) -> list[dict]:
        async with self.database.session() as session:
            return await self._list_skills(session, grades, areas, q)

    async def _list_skills(self, session, grades=None, areas=None, q=None) -> list[dict]:
        stmt = select(BnccSkill).where(BnccSkill.deleted == False)
        if grades:
            numbers = [n for n in (_grade_number(g) for g in grades) if n is not None]
            stmt = stmt.where(or_(*[and_(BnccSkill.grade_from <= n, BnccSkill.grade_to >= n) for n in numbers]) if numbers else False)
        if areas:
            stmt = stmt.where(BnccSkill.area.in_(areas))
        if q and q.strip():
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(BnccSkill.code.ilike(like), BnccSkill.description.ilike(like)))
        stmt = stmt.order_by(BnccSkill.grade_order, BnccSkill.grade, BnccSkill.position, BnccSkill.code)
        return [_skill_dict(s) for s in (await session.execute(stmt)).scalars().all()]

    async def _validate(self, session, data: dict, skill_id: Optional[str] = None) -> dict:
        clean = {k: (data.get(k) or "").strip() for k in ("area", "code", "description")}
        if not all(clean.values()):
            raise BnccError("Área, código e descrição são obrigatórios.")
        if len(clean["code"]) > 40:
            raise BnccError("O código pode ter no máximo 40 caracteres.")
        stage = data.get("stage") or "fundamental"
        if stage not in ("infantil", "fundamental"):
            raise BnccError("Etapa inválida.")
        clean["stage"] = stage
        if stage == "infantil":
            y_from = y_to = 0
        else:
            try:
                y_from, y_to = int(data.get("grade_from")), int(data.get("grade_to"))
            except (TypeError, ValueError):
                raise BnccError("Informe o ano inicial e o ano final.")
            if not 1 <= y_from <= y_to <= 5:
                raise BnccError("Os anos devem estar entre 1 e 5, com o ano inicial menor ou igual ao final.")
        clean["grade_from"], clean["grade_to"] = y_from, y_to
        infantil = (await session.execute(
            select(BnccSkill.grade).where(BnccSkill.stage == "infantil", BnccSkill.deleted == False).limit(1)  # noqa: E712
        )).scalar() or INFANTIL_LABEL
        clean["grade"] = _grade_label(stage, y_from, y_to, infantil)
        clean["grade_order"] = y_from
        dup = await session.execute(
            select(BnccSkill.id).where(
                BnccSkill.code == clean["code"], BnccSkill.deleted == False, BnccSkill.id != (skill_id or ""),  # noqa: E712
            )
        )
        if dup.first():
            raise BnccError("Já existe uma habilidade com esse código. Cada código é cadastrado uma única vez; use o ano inicial e o final.")
        return clean

    async def create_skill(self, data: dict) -> dict:
        async with self.database.session() as session:
            clean = await self._validate(session, data)
            last = (await session.execute(
                select(func.max(BnccSkill.position)).where(BnccSkill.grade_from == clean["grade_from"], BnccSkill.deleted == False)  # noqa: E712
            )).scalar()
            skill = BnccSkill(id=str(uuid.uuid4()), position=(last or 0) + 1, **clean)
            session.add(skill)
            await session.commit()
            await session.refresh(skill)
            return _skill_dict(skill)

    async def update_skill(self, skill_id: str, data: dict) -> Optional[dict]:
        async with self.database.session() as session:
            skill = await session.get(BnccSkill, skill_id)
            if not skill or skill.deleted:
                return None
            clean = await self._validate(session, data, skill_id)
            for k, v in clean.items():
                setattr(skill, k, v)
            await session.commit()
            await session.refresh(skill)
            return _skill_dict(skill)

    async def delete_skill(self, skill_id: str) -> bool:
        async with self.database.session() as session:
            skill = await session.get(BnccSkill, skill_id)
            if not skill or skill.deleted:
                return False
            skill.deleted = True
            await session.commit()
            return True

    # ── notas por aluno ───────────────────────────────────────────────────────

    async def student_skills(
        self, student_id: str, grades: Optional[list[str]] = None, areas: Optional[list[str]] = None,
        q: Optional[str] = None, min_score: Optional[int] = None, max_score: Optional[int] = None,
        only_with_observation: bool = False, only_in_plan: bool = False, actor: Optional[dict] = None,
    ) -> list[dict]:
        async with self.database.session() as session:
            skills = await self._list_skills(session, grades, areas, q)
            ids = [s["id"] for s in skills]
            scores: dict[str, StudentSkillScore] = {}
            if ids:
                rows = await session.execute(
                    select(StudentSkillScore).where(StudentSkillScore.student_id == student_id)
                )
                scores = {r.skill_id: r for r in rows.scalars().all()}
        out = []
        for s in skills:
            row = scores.get(s["id"])
            score = row.score if row else 0
            observation = (row.observation or "") if row else ""
            if min_score is not None and score < min_score:
                continue
            if max_score is not None and score > max_score:
                continue
            if only_with_observation and not observation.strip():
                continue
            if only_in_plan and not (row and row.in_plan):
                continue
            out.append({
                **s, "score": score, "observation": observation, **_plan_dict(row, actor),
                "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
            })
        return out

    async def set_score(self, student_id: str, skill_id: str, fields: dict, user: dict) -> dict:
        async with self.database.session() as session:
            if not await session.get(Student, student_id):
                raise BnccError("Aluno não encontrado.")
            skill = await session.get(BnccSkill, skill_id)
            if not skill or skill.deleted:
                raise BnccError("Habilidade não encontrada.")
            row = await session.get(StudentSkillScore, (student_id, skill_id))
            if not row:
                row = StudentSkillScore(
                    student_id=student_id, skill_id=skill_id, score=0, ai_excluded=False, in_plan=False,
                )
                session.add(row)
            old_score = row.score or 0
            if old_score >= 5 and user.get("role") not in LOCK_OVERRIDE_ROLES:
                raise BnccError("Habilidade com 5 estrelas: não pode mais ser alterada (peça à coordenação).")
            if "score" in fields and fields["score"] is not None:
                row.score = int(fields["score"])
            if "observation" in fields:
                row.observation = (fields["observation"] or "").strip() or None
            for key in ("summary", "adaptation", "justification"):
                if key in fields:
                    setattr(row, key, (fields[key] or "").strip() or None)
            if "adaptations" in fields:
                merged = merge_adaptations(
                    normalize_adaptations(row.actions), normalize_adaptations(fields["adaptations"]),
                    actor_from_user(user), await default_responsible(session, student_id),
                )
                row.actions = dump_adaptations(await fill_responsibles(session, merged))
            if "experience_fields" in fields:
                codes = [str(c).strip() for c in (fields["experience_fields"] or []) if str(c).strip()]
                row.correlated_codes = json.dumps(codes, ensure_ascii=False) if codes else None
            if "ai_excluded" in fields and fields["ai_excluded"] is not None:
                row.ai_excluded = bool(fields["ai_excluded"])
            if "in_plan" in fields and fields["in_plan"] is not None:
                was = bool(row.in_plan)
                row.in_plan = bool(fields["in_plan"])
                if row.in_plan != was:
                    session.add(StudentSkillEvent(
                        id=str(uuid.uuid4()), student_id=student_id, skill_id=skill_id, kind="plan",
                        old_score=old_score, new_score=row.score,
                        note="Habilidade incluída no plano." if row.in_plan else "Habilidade removida do plano.",
                        user_id=user.get("user_id"), username=user.get("username"),
                    ))
            row.updated_by_user_id = user.get("user_id")
            row.updated_by_username = user.get("username")
            if row.score != old_score:
                session.add(StudentSkillEvent(
                    id=str(uuid.uuid4()), student_id=student_id, skill_id=skill_id, kind="score",
                    old_score=old_score, new_score=row.score,
                    note=(fields.get("change_note") or "").strip() or None,
                    evidence_card_ids=json.dumps(fields.get("evidence_card_ids") or []) if fields.get("evidence_card_ids") else None,
                    user_id=user.get("user_id"), username=user.get("username"),
                ))
            await session.commit()
            await session.refresh(row)
            return {**_skill_dict(skill), "score": row.score, "observation": row.observation or "",
                    **_plan_dict(row, actor_from_user(user)),
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None}

    async def clear_events(self, student_id: str, skill_id: str, event_ids: Optional[list[str]]) -> dict:
        """Apaga registros da linha do tempo (todos, se `event_ids` for None) e recalcula a nota pelo que sobrou:
        a nota do último registro de nota restante, ou 0 se não sobrar nenhum (habilidade zerada)."""
        async with self.database.session() as session:
            query = select(StudentSkillEvent).where(
                StudentSkillEvent.student_id == student_id, StudentSkillEvent.skill_id == skill_id,
            )
            if event_ids is not None:
                query = query.where(StudentSkillEvent.id.in_(event_ids))
            doomed = (await session.execute(query)).scalars().all()
            for e in doomed:
                await session.delete(e)
            await session.flush()
            last = (await session.execute(
                select(StudentSkillEvent).where(
                    StudentSkillEvent.student_id == student_id, StudentSkillEvent.skill_id == skill_id,
                    StudentSkillEvent.kind == "score", StudentSkillEvent.new_score.is_not(None),
                ).order_by(StudentSkillEvent.created_at.desc()).limit(1)
            )).scalars().first()
            score = last.new_score if last else 0
            row = await session.get(StudentSkillScore, (student_id, skill_id))
            if row:
                row.score = score
            await session.commit()
            return {"deleted": len(doomed), "score": score}

    async def list_events(self, student_id: str, skill_id: str) -> list[dict]:
        async with self.database.session() as session:
            rows = await session.execute(
                select(StudentSkillEvent)
                .where(StudentSkillEvent.student_id == student_id, StudentSkillEvent.skill_id == skill_id)
                .order_by(StudentSkillEvent.created_at.desc())
            )
            return [{
                "id": e.id, "kind": e.kind, "old_score": e.old_score, "new_score": e.new_score,
                "note": e.note, "evidence_card_ids": _load_codes(e.evidence_card_ids),
                "username": e.username, "created_at": e.created_at.isoformat() if e.created_at else None,
            } for e in rows.scalars().all()]

    # ── relatórios ────────────────────────────────────────────────────────────

    async def create_report(self, student_id: str, filters: dict, user: dict) -> dict:
        grades = filters.get("grades") or None
        areas = filters.get("areas") or None
        include_obs = bool(filters.get("include_observations", True))
        items = await self.student_skills(
            student_id, grades=grades, areas=areas, q=filters.get("query"),
            min_score=filters.get("min_score"), max_score=filters.get("max_score"),
            only_with_observation=bool(filters.get("only_with_observation")),
        )
        by_score = {str(n): 0 for n in range(6)}
        for it in items:
            by_score[str(it["score"])] += 1
        groups: list[dict] = []
        for it in items:
            if not groups or groups[-1]["grade"] != it["grade"]:
                groups.append({"grade": it["grade"], "areas": []})
            areas_list = groups[-1]["areas"]
            if not areas_list or areas_list[-1]["area"] != it["area"]:
                areas_list.append({"area": it["area"], "skills": []})
            skill = {"code": it["code"], "description": it["description"], "score": it["score"]}
            if include_obs and it["observation"]:
                skill["observation"] = it["observation"]
            areas_list[-1]["skills"].append(skill)
        content = {
            "version": 1,
            "type": "bncc_skills_report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "student_id": student_id,
            "filters": {
                "grades": grades or [], "areas": areas or [],
                "min_score": filters.get("min_score"), "max_score": filters.get("max_score"),
                "include_observations": include_obs,
                "only_with_observation": bool(filters.get("only_with_observation")),
                "query": (filters.get("query") or "").strip() or None,
            },
            "summary": {
                "total": len(items), "by_score": by_score,
                "average": round(sum(i["score"] for i in items) / len(items), 2) if items else 0,
            },
            "groups": groups,
        }
        title = (filters.get("title") or "").strip() or self._default_title(content["filters"])
        async with self.database.session() as session:
            if not await session.get(Student, student_id):
                raise BnccError("Aluno não encontrado.")
            report = SkillReport(
                id=str(uuid.uuid4()), student_id=student_id, title=title[:255],
                content=json.dumps(content, ensure_ascii=False),
                created_by_user_id=user.get("user_id"), created_by_username=user.get("username"),
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return self._report_dict(report, content)

    @staticmethod
    def _default_title(f: dict) -> str:
        parts = []
        parts.append(", ".join(f["grades"]) if f["grades"] else "todos os anos")
        if f["min_score"] is not None or f["max_score"] is not None:
            lo = f["min_score"] if f["min_score"] is not None else 0
            hi = f["max_score"] if f["max_score"] is not None else 5
            parts.append(f"notas {lo} a {hi}")
        return "Habilidades BNCC — " + " · ".join(parts)

    @staticmethod
    def _report_dict(r: SkillReport, content: Optional[dict] = None, with_content: bool = True) -> dict:
        if content is None:
            try:
                content = json.loads(r.content)
            except Exception:
                content = {}
        out = {
            "id": r.id, "student_id": r.student_id, "title": r.title,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "created_by": r.created_by_username,
            "filters": content.get("filters", {}), "summary": content.get("summary", {}),
        }
        if with_content:
            out["content"] = content
        return out

    async def list_reports(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            rows = await session.execute(
                select(SkillReport).where(SkillReport.student_id == student_id, SkillReport.deleted == False)
                .order_by(SkillReport.created_at.desc())
            )
            return [self._report_dict(r, with_content=False) for r in rows.scalars().all()]

    async def get_report(self, report_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            r = await session.get(SkillReport, report_id)
            return self._report_dict(r) if r and not r.deleted else None

    async def delete_report(self, report_id: str) -> bool:
        async with self.database.session() as session:
            r = await session.get(SkillReport, report_id)
            if not r or r.deleted:
                return False
            r.deleted = True
            await session.commit()
            return True
