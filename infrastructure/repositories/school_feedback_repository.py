from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.school_feedback import SchoolFeedback


class SchoolFeedbackRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, school_feedback: SchoolFeedback) -> SchoolFeedback:
        async with self.database.session() as session:
            session.add(school_feedback)
            await session.commit()
            await session.refresh(school_feedback)

            return school_feedback

    async def verify(self, entity: SchoolFeedback) -> SchoolFeedback | None:
        async with self.database.session() as session:
            stmt = select(SchoolFeedback).filter_by(
                beneficiary_id=entity.beneficiary_id,
                supervisor_id=entity.supervisor_id,
                feedback_date=entity.feedback_date,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[SchoolFeedback]:
        async with self.database.session() as session:
            result = await session.execute(select(SchoolFeedback))
            return result.scalars().all()

    async def get_by_id(self, school_feedback_id: int) -> SchoolFeedback | None:
        async with self.database.session() as session:
            stmt = select(SchoolFeedback).filter_by(id=school_feedback_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, school_feedback: SchoolFeedback) -> SchoolFeedback:
        try:
            async with self.database.session() as session:
                merged_school_feedback = await session.merge(school_feedback)
                await session.commit()
                await session.refresh(merged_school_feedback)

                return merged_school_feedback
        except Exception as e:
            raise e

    async def delete(self, school_feedback: SchoolFeedback) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(school_feedback)
                await session.commit()
        except Exception as e:
            raise e
