from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.therapeutic_plan import TherapeuticPlan


class TherapeuticPlanRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, therapeutic_plan: TherapeuticPlan) -> TherapeuticPlan:
        async with self.database.session() as session:
            session.add(therapeutic_plan)
            await session.commit()
            await session.refresh(therapeutic_plan)

            return therapeutic_plan

    async def verify(self, entity: TherapeuticPlan) -> TherapeuticPlan | None:
        async with self.database.session() as session:
            stmt = select(TherapeuticPlan).filter_by(
                beneficiary_id=entity.beneficiary_id,
                start_date=entity.start_date,
                end_date=entity.end_date,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[TherapeuticPlan]:
        async with self.database.session() as session:
            result = await session.execute(select(TherapeuticPlan))
            return result.scalars().all()

    async def get_by_id(self, therapeutic_plan_id: int) -> TherapeuticPlan | None:
        async with self.database.session() as session:
            stmt = select(TherapeuticPlan).filter_by(id=therapeutic_plan_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, therapeutic_plan: TherapeuticPlan) -> TherapeuticPlan:
        try:
            async with self.database.session() as session:
                merged_therapeutic_plan = await session.merge(therapeutic_plan)
                await session.commit()
                await session.refresh(merged_therapeutic_plan)

                return merged_therapeutic_plan
        except Exception as e:
            raise e

    async def delete(self, therapeutic_plan: TherapeuticPlan) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(therapeutic_plan)
                await session.commit()
        except Exception as e:
            raise e
