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

    async def update(self, school_feedback_id: int, **kwargs) -> SchoolFeedback | None:
        try:
            async with self.database.session() as session:
                stmt = select(SchoolFeedback).filter_by(id=school_feedback_id)
                result = await session.execute(stmt)
                existing_feedback = result.scalars().first()

                if not existing_feedback:
                    return None

                for key, value in kwargs.items():
                    if hasattr(existing_feedback, key):
                        setattr(existing_feedback, key, value)

                await session.commit()
                await session.refresh(existing_feedback)

                return existing_feedback
        except Exception as e:
            raise e

    async def delete(self, school_feedback_id: int) -> bool:
        try:
            async with self.database.session() as session:
                stmt = select(SchoolFeedback).filter_by(id=school_feedback_id)
                result = await session.execute(stmt)
                school_feedback = result.scalars().first()

                if not school_feedback:
                    return False

                await session.delete(school_feedback)
                await session.commit()
                return True
        except Exception as e:
            raise e
