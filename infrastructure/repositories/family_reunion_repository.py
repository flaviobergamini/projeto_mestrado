from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.family_reunion import FamilyReunion


class FamilyReunionRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, family_reunion: FamilyReunion) -> FamilyReunion:
        async with self.database.session() as session:
            session.add(family_reunion)
            await session.commit()
            await session.refresh(family_reunion)

            return family_reunion

    async def verify(self, entity: FamilyReunion) -> FamilyReunion | None:
        async with self.database.session() as session:
            stmt = select(FamilyReunion).filter_by(
                beneficiary_id=entity.beneficiary_id,
                supervisor_id=entity.supervisor_id,
                reunion_date=entity.reunion_date,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[FamilyReunion]:
        async with self.database.session() as session:
            result = await session.execute(select(FamilyReunion))
            return result.scalars().all()

    async def get_by_id(self, family_reunion_id: int) -> FamilyReunion | None:
        async with self.database.session() as session:
            stmt = select(FamilyReunion).filter_by(id=family_reunion_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, family_reunion: FamilyReunion) -> FamilyReunion:
        try:
            async with self.database.session() as session:
                merged_family_reunion = await session.merge(family_reunion)
                await session.commit()
                await session.refresh(merged_family_reunion)

                return merged_family_reunion
        except Exception as e:
            raise e

    async def delete(self, family_reunion: FamilyReunion) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(family_reunion)
                await session.commit()
        except Exception as e:
            raise e
