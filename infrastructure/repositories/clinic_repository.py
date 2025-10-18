from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.clinic import Clinic


class ClinicRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, clinic: Clinic) -> Clinic:
        async with self.database.session() as session:
            session.add(clinic)
            await session.commit()
            await session.refresh(clinic)

            return clinic

    async def verify(self, entity: Clinic) -> Clinic | None:
        async with self.database.session() as session:
            stmt = select(Clinic).filter_by(
                name=entity.name,
                address=entity.address,
                telephone=entity.telephone,
                email=entity.email,
                responsible=entity.responsible,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[Clinic]:
        async with self.database.session() as session:
            result = await session.execute(select(Clinic))
            return result.scalars().all()

    async def get_by_id(self, clinic_id: int) -> Clinic | None:
        async with self.database.session() as session:
            stmt = select(Clinic).filter_by(id=clinic_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, clinic: Clinic) -> Clinic:
        try:
            async with self.database.session() as session:
                merged_clinic = await session.merge(clinic)
                await session.commit()
                await session.refresh(merged_clinic)

                return merged_clinic
        except Exception as e:
            raise e

    async def delete(self, clinic: Clinic) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(clinic)
                await session.commit()
        except Exception as e:
            raise e
