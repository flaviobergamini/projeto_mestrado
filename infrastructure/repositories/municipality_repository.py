import uuid
from sqlalchemy import select, delete, func
from infrastructure.database_context.database import Database
from infrastructure.models.municipality import Municipality


class MunicipalityRepository:
    def __init__(self, database: Database):
        self._db = database

    async def list_all(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(select(Municipality).where(Municipality.deleted == False).order_by(Municipality.name))
            return [self._to_dict(r) for r in result.scalars().all()]

    async def get_by_id(self, municipality_id: str) -> dict | None:
        async with self._db.session() as session:
            result = await session.execute(select(Municipality).where(Municipality.id == municipality_id, Municipality.deleted == False))
            row = result.scalar_one_or_none()
            return self._to_dict(row) if row else None

    async def create(self, name: str) -> dict:
        async with self._db.session() as session:
            row = Municipality(id=str(uuid.uuid4()), name=name)
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._to_dict(row)

    async def update(self, municipality_id: str, name: str) -> dict | None:
        async with self._db.session() as session:
            result = await session.execute(select(Municipality).where(Municipality.id == municipality_id))
            row = result.scalar_one_or_none()
            if not row:
                return None
            row.name = name
            await session.commit()
            await session.refresh(row)
            return self._to_dict(row)

    async def delete(self, municipality_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(select(Municipality).where(Municipality.id == municipality_id, Municipality.deleted == False))
            row = result.scalar_one_or_none()
            if not row:
                return False
            row.deleted = True
            await session.commit()
            return True

    def _to_dict(self, row: Municipality) -> dict:
        return {
            "id": row.id,
            "name": row.name,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
