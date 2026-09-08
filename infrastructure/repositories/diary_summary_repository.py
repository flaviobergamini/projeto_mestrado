import uuid
from typing import Optional
from sqlalchemy import select, desc

from infrastructure.database_context.database import Database
from infrastructure.models.diary_summary import DiarySummary


def _to_dict(s: DiarySummary) -> dict:
    return {
        "id": s.id,
        "student_id": s.student_id,
        "author_user_id": s.author_user_id,
        "period_start": s.period_start,
        "period_end": s.period_end,
        "summary_text": s.summary_text,
        "source_entries": s.source_entries or [],
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


class DiarySummaryRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def create(
        self,
        student_id: str,
        author_user_id: str,
        period_start: Optional[str],
        period_end: Optional[str],
        summary_text: str,
        source_entries: list,
    ) -> dict:
        async with self.database.session() as session:
            obj = DiarySummary(
                id=str(uuid.uuid4()),
                student_id=student_id,
                author_user_id=author_user_id,
                period_start=period_start,
                period_end=period_end,
                summary_text=summary_text,
                source_entries=source_entries,
            )

            session.add(obj)

            await session.commit()

            await session.refresh(obj)

            return _to_dict(obj)

    async def list_by_student(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(DiarySummary)
                .where(DiarySummary.student_id == student_id, DiarySummary.deleted == False)
                .order_by(desc(DiarySummary.created_at))
            )

            return [_to_dict(s) for s in result.scalars().all()]

    async def get_by_id(self, summary_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(DiarySummary).where(DiarySummary.id == summary_id, DiarySummary.deleted == False)
            )

            s = result.scalars().first()

            return _to_dict(s) if s else None

    async def delete(self, summary_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(
                select(DiarySummary).where(DiarySummary.id == summary_id, DiarySummary.deleted == False)
            )

            s = result.scalars().first()

            if not s:
                return False

            s.deleted = True

            await session.commit()

            return True
