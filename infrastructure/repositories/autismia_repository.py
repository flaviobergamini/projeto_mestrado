from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.autismia import Autismia


class AutismiaRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, autismia: Autismia) -> Autismia:
        async with self.database.session() as session:
            session.add(autismia)
            await session.commit()
            await session.refresh(autismia)

            return autismia

    async def verify(self, entity: Autismia) -> Autismia | None:
        async with self.database.session() as session:
            stmt = select(Autismia).filter_by(
                name=entity.name,
                address=entity.address,
                telephone=entity.telephone,
                email=entity.email,
                responsible=entity.responsible,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[Autismia]:
        async with self.database.session() as session:
            result = await session.execute(select(Autismia))
            return result.scalars().all()

    async def get_by_id(self, autismia_id: int) -> Autismia | None:
        async with self.database.session() as session:
            stmt = select(Autismia).filter_by(id=autismia_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, autismia: Autismia) -> Autismia:
        try:
            async with self.database.session() as session:
                merged_autismia = await session.merge(autismia)
                await session.commit()
                await session.refresh(merged_autismia)

                return merged_autismia
        except Exception as e:
            raise e

    async def delete(self, autismia: Autismia) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(autismia)
                await session.commit()
        except Exception as e:
            raise e
