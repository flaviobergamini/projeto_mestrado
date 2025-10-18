from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.therapeutic_sessions import TherapeuticSessions


class TherapeuticSessionsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, therapeutic_sessions: TherapeuticSessions) -> TherapeuticSessions:
        async with self.database.session() as session:
            session.add(therapeutic_sessions)
            await session.commit()
            await session.refresh(therapeutic_sessions)

            return therapeutic_sessions

    async def verify(self, entity: TherapeuticSessions) -> TherapeuticSessions | None:
        async with self.database.session() as session:
            stmt = select(TherapeuticSessions).filter_by(
                therapeutic_plan_id=entity.therapeutic_plan_id,
                professional_id=entity.professional_id,
                clinic_id=entity.clinic_id,
                session_date=entity.session_date,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[TherapeuticSessions]:
        async with self.database.session() as session:
            result = await session.execute(select(TherapeuticSessions))
            return result.scalars().all()

    async def get_by_id(self, therapeutic_sessions_id: int) -> TherapeuticSessions | None:
        async with self.database.session() as session:
            stmt = select(TherapeuticSessions).filter_by(id=therapeutic_sessions_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, therapeutic_sessions: TherapeuticSessions) -> TherapeuticSessions:
        try:
            async with self.database.session() as session:
                merged_therapeutic_sessions = await session.merge(therapeutic_sessions)
                await session.commit()
                await session.refresh(merged_therapeutic_sessions)

                return merged_therapeutic_sessions
        except Exception as e:
            raise e

    async def delete(self, therapeutic_sessions: TherapeuticSessions) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(therapeutic_sessions)
                await session.commit()
        except Exception as e:
            raise e
