import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func, or_
from infrastructure.database_context.database import Database
from infrastructure.models.bncc import BnccSkill, StudentSkillScore, SkillReport
from infrastructure.models.student import Student


class BnccError(ValueError):
    pass


def _skill_dict(s: BnccSkill) -> dict:
    return {
        "id": s.id, "stage": s.stage, "grade": s.grade, "grade_order": s.grade_order,
        "area": s.area, "code": s.code, "description": s.description, "position": s.position,
    }


def _grade_order(grade: str, stage: str) -> int:
    if stage == "infantil":
        return 0
    m = re.match(r"\s*(\d+)", grade)
    return int(m.group(1)) if m else 99


class BnccRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    # ── catálogo ──────────────────────────────────────────────────────────────

    async def list_grades(self) -> list[dict]:
        async with self.database.session() as session:
            rows = await session.execute(
                select(BnccSkill.grade, BnccSkill.grade_order, BnccSkill.stage, func.count(BnccSkill.id))
                .where(BnccSkill.deleted == False)
                .group_by(BnccSkill.grade, BnccSkill.grade_order, BnccSkill.stage)
                .order_by(BnccSkill.grade_order, BnccSkill.grade)
            )
            return [{"grade": g, "grade_order": o, "stage": st, "count": n} for g, o, st, n in rows.all()]

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
            stmt = stmt.where(BnccSkill.grade.in_(grades))
        if areas:
            stmt = stmt.where(BnccSkill.area.in_(areas))
        if q and q.strip():
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(BnccSkill.code.ilike(like), BnccSkill.description.ilike(like)))
        stmt = stmt.order_by(BnccSkill.grade_order, BnccSkill.grade, BnccSkill.position, BnccSkill.code)
        return [_skill_dict(s) for s in (await session.execute(stmt)).scalars().all()]

    async def _validate(self, session, data: dict, skill_id: Optional[str] = None) -> dict:
        clean = {k: (data.get(k) or "").strip() for k in ("grade", "area", "code", "description")}
        if not all(clean.values()):
            raise BnccError("Ano, área, código e descrição são obrigatórios.")
        if len(clean["code"]) > 40:
            raise BnccError("O código pode ter no máximo 40 caracteres.")
        stage = data.get("stage") or "fundamental"
        if stage not in ("infantil", "fundamental"):
            raise BnccError("Etapa inválida.")
        clean["stage"] = stage
        dup = await session.execute(
            select(BnccSkill.id).where(
                BnccSkill.grade == clean["grade"], BnccSkill.code == clean["code"],
                BnccSkill.deleted == False, BnccSkill.id != (skill_id or ""),
            )
        )
        if dup.first():
            raise BnccError("Já existe uma habilidade com esse código neste ano.")
        return clean

    async def create_skill(self, data: dict) -> dict:
        async with self.database.session() as session:
            clean = await self._validate(session, data)
            same_grade = (await session.execute(
                select(BnccSkill.grade_order, func.max(BnccSkill.position))
                .where(BnccSkill.grade == clean["grade"], BnccSkill.deleted == False)
                .group_by(BnccSkill.grade_order)
            )).first()
            order = same_grade[0] if same_grade else _grade_order(clean["grade"], clean["stage"])
            position = (same_grade[1] or 0) + 1 if same_grade else 1
            skill = BnccSkill(id=str(uuid.uuid4()), grade_order=order, position=position, **clean)
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
            known = await self._known_grades(session)
            order = known.get(clean["grade"], _grade_order(clean["grade"], clean["stage"]))
            for k, v in clean.items():
                setattr(skill, k, v)
            skill.grade_order = order
            await session.commit()
            await session.refresh(skill)
            return _skill_dict(skill)

    async def _known_grades(self, session) -> dict[str, int]:
        rows = await session.execute(
            select(BnccSkill.grade, BnccSkill.grade_order).where(BnccSkill.deleted == False).distinct()
        )
        return {g: o for g, o in rows.all()}

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
        only_with_observation: bool = False,
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
            out.append({
                **s, "score": score, "observation": observation,
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
                row = StudentSkillScore(student_id=student_id, skill_id=skill_id, score=0)
                session.add(row)
            if "score" in fields and fields["score"] is not None:
                row.score = int(fields["score"])
            if "observation" in fields:
                row.observation = (fields["observation"] or "").strip() or None
            row.updated_by_user_id = user.get("user_id")
            row.updated_by_username = user.get("username")
            await session.commit()
            await session.refresh(row)
            return {**_skill_dict(skill), "score": row.score, "observation": row.observation or "",
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None}

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
