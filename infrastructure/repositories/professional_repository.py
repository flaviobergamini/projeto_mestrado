from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.professional import Professional


class ProfessionalRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, professional: Professional) -> Professional:
        async with self.database.session() as session:
            session.add(professional)
            await session.commit()
            await session.refresh(professional)

            return professional

    async def verify(self, entity: Professional) -> Professional | None:
        async with self.database.session() as session:
            stmt = select(Professional).filter_by(
                name=entity.name,
                email=entity.email,
                clinic_id=entity.clinic_id,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[Professional]:
        async with self.database.session() as session:
            result = await session.execute(select(Professional))
            return result.scalars().all()

    async def get_by_id(self, professional_id: int) -> Professional | None:
        async with self.database.session() as session:
            stmt = select(Professional).filter_by(id=professional_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_by_clinic(self, clinic_id: int) -> list[Professional]:
        async with self.database.session() as session:
            stmt = select(Professional).filter_by(clinic_id=clinic_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update(self, professional: Professional) -> Professional:
        try:
            async with self.database.session() as session:
                merged_professional = await session.merge(professional)
                await session.commit()
                await session.refresh(merged_professional)

                return merged_professional
        except Exception as e:
            raise e

    async def delete(self, professional: Professional) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(professional)
                await session.commit()
        except Exception as e:
            raise e
