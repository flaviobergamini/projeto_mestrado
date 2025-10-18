from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.evaluation import Evaluation


class EvaluationRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, evaluation: Evaluation) -> Evaluation:
        async with self.database.session() as session:
            session.add(evaluation)
            await session.commit()
            await session.refresh(evaluation)

            return evaluation

    async def verify(self, entity: Evaluation) -> Evaluation | None:
        async with self.database.session() as session:
            stmt = select(Evaluation).filter_by(
                beneficiary_id=entity.beneficiary_id,
                date=entity.date,
                type=entity.type,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[Evaluation]:
        async with self.database.session() as session:
            result = await session.execute(select(Evaluation))
            return result.scalars().all()

    async def get_by_id(self, evaluation_id: int) -> Evaluation | None:
        async with self.database.session() as session:
            stmt = select(Evaluation).filter_by(id=evaluation_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, evaluation: Evaluation) -> Evaluation:
        try:
            async with self.database.session() as session:
                merged_evaluation = await session.merge(evaluation)
                await session.commit()
                await session.refresh(merged_evaluation)

                return merged_evaluation
        except Exception as e:
            raise e

    async def delete(self, evaluation: Evaluation) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(evaluation)
                await session.commit()
        except Exception as e:
            raise e
