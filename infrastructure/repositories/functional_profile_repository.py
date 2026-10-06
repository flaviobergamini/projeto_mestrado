import json
import uuid
from datetime import date
from typing import Optional
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.functional_profile import FunctionalProfile
from infrastructure.models.student import Student
from core.interfaces.i_functional_profile_repository import IFunctionalProfileRepository, ProfileError
from core.services.functional_profile_content import normalize_content, average_level
from core.constants.functional_profile import DOMAINS


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        raise ProfileError("Data inválida (use AAAA-MM-DD).")


def _ref_date(p: FunctionalProfile) -> date:
    return p.period_end or (p.created_at.date() if p.created_at else date.today())


class FunctionalProfileRepository(IFunctionalProfileRepository):
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _dict(p: FunctionalProfile, with_content: bool = True) -> dict:
        try:
            content = json.loads(p.content)
        except Exception:
            content = normalize_content({})
        out = {
            "id": p.id, "student_id": p.student_id, "title": p.title,
            "period_start": p.period_start.isoformat() if p.period_start else None,
            "period_end": p.period_end.isoformat() if p.period_end else None,
            "origin": p.origin,
            "sources": json.loads(p.sources) if p.sources else [],
            "created_by": p.created_by_username, "edited_by": p.edited_by_username,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "average_level": average_level(content),
            "levels": {d["key"]: d["level"] for d in content["domains"]},
        }
        if with_content:
            out["content"] = content
        return out

    async def create(self, student_id: str, content: dict, origin: str, user: dict, title: Optional[str] = None,
                     period_start: Optional[str] = None, period_end: Optional[str] = None,
                     sources: Optional[list[str]] = None) -> dict:
        ps, pe = _parse_date(period_start), _parse_date(period_end)
        if ps and pe and ps > pe:
            raise ProfileError("A data inicial não pode ser depois da final.")
        content = normalize_content(content)
        async with self.database.session() as session:
            if not await session.get(Student, student_id):
                raise ProfileError("Aluno não encontrado.")
            ref = pe or date.today()
            profile = FunctionalProfile(
                id=str(uuid.uuid4()), student_id=student_id,
                title=(title or "").strip()[:255] or f"Perfil funcional — {ref.strftime('%d/%m/%Y')}",
                period_start=ps, period_end=pe, origin=origin,
                sources=json.dumps(sources or [], ensure_ascii=False),
                content=json.dumps(content, ensure_ascii=False),
                created_by_user_id=user.get("user_id"), created_by_username=user.get("username"),
            )
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            return self._dict(profile)

    async def update(self, profile_id: str, content: Optional[dict], user: dict, title: Optional[str] = None,
                     period_start: Optional[str] = None, period_end: Optional[str] = None,
                     fields_set: Optional[set] = None) -> Optional[dict]:
        fields_set = fields_set or set()
        async with self.database.session() as session:
            p = await session.get(FunctionalProfile, profile_id)
            if not p or p.deleted:
                return None
            if content is not None:
                p.content = json.dumps(normalize_content(content), ensure_ascii=False)
            if title is not None and title.strip():
                p.title = title.strip()[:255]
            if "period_start" in fields_set:
                p.period_start = _parse_date(period_start)
            if "period_end" in fields_set:
                p.period_end = _parse_date(period_end)
            if p.period_start and p.period_end and p.period_start > p.period_end:
                raise ProfileError("A data inicial não pode ser depois da final.")
            p.edited_by_username = user.get("username")
            await session.commit()
            await session.refresh(p)
            return self._dict(p)

    async def list_for_student(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            rows = await session.execute(
                select(FunctionalProfile).where(FunctionalProfile.student_id == student_id, FunctionalProfile.deleted == False)
            )
            profiles = sorted(rows.scalars().all(), key=lambda p: (_ref_date(p), p.created_at), reverse=True)
            return [self._dict(p, with_content=False) for p in profiles]

    async def get(self, profile_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            p = await session.get(FunctionalProfile, profile_id)
            return self._dict(p) if p and not p.deleted else None

    async def delete(self, profile_id: str) -> bool:
        async with self.database.session() as session:
            p = await session.get(FunctionalProfile, profile_id)
            if not p or p.deleted:
                return False
            p.deleted = True
            await session.commit()
            return True

    async def latest(self, student_id: str) -> Optional[dict]:
        items = await self.list_for_student(student_id)
        return await self.get(items[0]["id"]) if items else None

    async def evolution(self, student_id: str) -> dict:
        """Perfil temporal: nível de cada domínio ao longo dos perfis salvos (ordem cronológica)."""
        async with self.database.session() as session:
            rows = await session.execute(
                select(FunctionalProfile).where(FunctionalProfile.student_id == student_id, FunctionalProfile.deleted == False)
            )
            profiles = sorted(rows.scalars().all(), key=lambda p: (_ref_date(p), p.created_at))
            snaps = [self._dict(p, with_content=False) for p in profiles]
        for s, p in zip(snaps, profiles):
            s["date"] = _ref_date(p).isoformat()
        domains = []
        for key, label in DOMAINS:
            series = [{"profile_id": s["id"], "date": s["date"], "level": s["levels"].get(key)} for s in snaps]
            known = [pt["level"] for pt in series if pt["level"] is not None]
            delta = known[-1] - known[0] if len(known) >= 2 else None
            domains.append({"key": key, "label": label, "series": series,
                            "first": known[0] if known else None, "last": known[-1] if known else None, "delta": delta})
        averages = [{"profile_id": s["id"], "date": s["date"], "level": s["average_level"]} for s in snaps]
        return {
            "profiles": [{k: s[k] for k in ("id", "title", "date", "origin", "average_level")} for s in snaps],
            "domains": domains, "average": averages,
        }
