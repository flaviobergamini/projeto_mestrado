import uuid
from datetime import date, datetime, time, timedelta
from typing import Optional
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.saved_skill_result import SavedSkillResult


def _to_dict(r: SavedSkillResult) -> dict:
    return {
        "id": r.id,
        "student_id": r.student_id,
        "skill_id": r.skill_id,
        "skill_title": r.skill_title,
        "response": r.response,
        "session_id": r.session_id,
        "saved_by_user_id": r.saved_by_user_id,
        "saved_by_username": r.saved_by_username,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


class SavedSkillResultRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def list_by_student(
        self,
        student_id: str,
        skill_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[dict]:
        """Sempre escopado por aluno no banco — nunca lista resultados de outros alunos."""
        async with self.database.session() as session:
            filters = [SavedSkillResult.student_id == student_id, SavedSkillResult.deleted == False]  # noqa: E712
            if skill_id:
                filters.append(SavedSkillResult.skill_id == skill_id)
            if date_from:
                filters.append(SavedSkillResult.created_at >= datetime.combine(date_from, time.min))
            if date_to:
                # inclusivo no dia final inteiro
                filters.append(SavedSkillResult.created_at < datetime.combine(date_to + timedelta(days=1), time.min))
            result = await session.execute(
                select(SavedSkillResult).where(*filters).order_by(SavedSkillResult.created_at.desc())
            )
            return [_to_dict(r) for r in result.scalars().all()]

    async def get_by_id(self, result_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(SavedSkillResult).where(SavedSkillResult.id == result_id, SavedSkillResult.deleted == False)  # noqa: E712
            )
            row = result.scalars().first()
            return _to_dict(row) if row else None

    async def create(self, data: dict) -> dict:
        async with self.database.session() as session:
            row = SavedSkillResult(
                id=str(uuid.uuid4()),
                student_id=data["student_id"],
                skill_id=data.get("skill_id"),
                skill_title=data["skill_title"],
                response=data["response"],
                session_id=data.get("session_id"),
                saved_by_user_id=data.get("saved_by_user_id"),
                saved_by_username=data.get("saved_by_username"),
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_dict(row)

    async def delete(self, result_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(
                select(SavedSkillResult).where(SavedSkillResult.id == result_id, SavedSkillResult.deleted == False)  # noqa: E712
            )
            row = result.scalars().first()
            if not row:
                return False
            row.deleted = True
            await session.commit()
            return True
