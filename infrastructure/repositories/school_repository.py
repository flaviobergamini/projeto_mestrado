import uuid
from typing import Optional
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.school import School


class SchoolRepository:
    def __init__(self, database: Database):
        self._db = database

    def _to_dict(self, s: School) -> dict:
        return {
            "id": s.id,
            "name": s.name,
            "cnpj": s.cnpj,
            "institution_type": s.institution_type,
            "address_city": s.address_city,
            "notes": s.notes,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }

    async def list_all(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(select(School).order_by(School.name))

            return [self._to_dict(s) for s in result.scalars().all()]

    async def get_by_id(self, school_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(select(School).where(School.id == school_id))

            s = result.scalar_one_or_none()

            return self._to_dict(s) if s else None

    async def create(self, data: dict) -> dict:
        async with self._db.session() as session:
            school = School(
                id=str(uuid.uuid4()),
                name=data["name"],
                cnpj=data.get("cnpj"),
                institution_type=data.get("institution_type"),
                address_city=data.get("address_city"),
                notes=data.get("notes"),
            )

            session.add(school)

            await session.commit()

            await session.refresh(school)

            return self._to_dict(school)

    async def update(self, school_id: str, data: dict) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(select(School).where(School.id == school_id))

            school = result.scalar_one_or_none()

            if not school:
                return None
            
            for field in ("name", "cnpj", "institution_type", "address_city", "notes"):
                if field in data:
                    setattr(school, field, data[field])

            await session.commit()

            await session.refresh(school)

            return self._to_dict(school)

    async def delete(self, school_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(select(School).where(School.id == school_id))

            school = result.scalar_one_or_none()

            if not school:
                return False
            
            await session.delete(school)

            await session.commit()
            
            return True
