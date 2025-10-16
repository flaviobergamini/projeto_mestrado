from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.supervisor import Supervisor


class SupervisorRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, supervisor: Supervisor) -> Supervisor:
        async with self.database.session() as session:
            session.add(supervisor)
            await session.commit()
            await session.refresh(supervisor)

            return supervisor

    async def verify(self, entity: Supervisor) -> Supervisor | None:
        async with self.database.session() as session:
            stmt = select(Supervisor).filter_by(
                name=entity.name,
                email=entity.email,
                contact=entity.contact,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[Supervisor]:
        async with self.database.session() as session:
            result = await session.execute(select(Supervisor))
            return result.scalars().all()

    async def get_by_id(self, supervisor_id: int) -> Supervisor | None:
        async with self.database.session() as session:
            stmt = select(Supervisor).filter_by(id=supervisor_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, supervisor: Supervisor) -> Supervisor:
        try:
            async with self.database.session() as session:
                merged_supervisor = await session.merge(supervisor)
                await session.commit()
                await session.refresh(merged_supervisor)

                return merged_supervisor
        except Exception as e:
            raise e

    async def delete(self, supervisor: Supervisor) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(supervisor)
                await session.commit()
        except Exception as e:
            raise e
