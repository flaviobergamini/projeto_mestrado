import json
import uuid
from sqlalchemy import select, delete

from infrastructure.database_context.database import Database
from infrastructure.models.generated_pei import GeneratedPei


class GeneratedPeiRepository:
    def __init__(self, database: Database):
        self._db = database

    async def save(
        self,
        student_id: str,
        student_name: str,
        pei_text: str,
        sources_used: list[str] | None = None,
        generated_by: str | None = None,
    ) -> dict:
        async with self._db.session() as session:
            row = GeneratedPei(
                id=str(uuid.uuid4()),
                student_id=student_id,
                student_name=student_name,
                pei_text=pei_text,
                sources_used=json.dumps(sources_used) if sources_used else None,
                generated_by=generated_by,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._to_dict(row)

    async def list_by_student(self, student_id: str) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(GeneratedPei)
                .where(GeneratedPei.student_id == student_id)
                .order_by(GeneratedPei.generated_at.desc())
            )
            return [self._to_dict(r) for r in result.scalars().all()]

    async def get_by_id(self, pei_id: str) -> dict | None:
        async with self._db.session() as session:
            result = await session.execute(
                select(GeneratedPei).where(GeneratedPei.id == pei_id)
            )
            row = result.scalar_one_or_none()
            return self._to_dict(row) if row else None

    async def delete(self, pei_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(
                select(GeneratedPei).where(GeneratedPei.id == pei_id)
            )
            row = result.scalar_one_or_none()
            if not row:
                return False
            await session.execute(delete(GeneratedPei).where(GeneratedPei.id == pei_id))
            await session.commit()
            return True

    def _to_dict(self, row: GeneratedPei) -> dict:
        sources = []
        try:
            sources = json.loads(row.sources_used) if row.sources_used else []
        except Exception:
            pass
        return {
            "id": row.id,
            "student_id": row.student_id,
            "student_name": row.student_name,
            "pei_text": row.pei_text,
            "sources_used": sources,
            "generated_by": row.generated_by,
            "generated_at": row.generated_at.isoformat() if row.generated_at else None,
        }
