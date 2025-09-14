import numpy as np
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.health_plan import HealthPlan


class HealthPlanRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, school: HealthPlan) -> HealthPlan:
        async with self.database.session() as session:
            session.add(school)
            await session.commit()
            await session.refresh(school)
            
            return school
        
    async def get_by_id(self, id: int) -> HealthPlan | None:
        async with self.database.session() as session:
            result = await session.execute(select(HealthPlan).where(HealthPlan.id == id))
            return result.scalars().first()
        
    async def verify(self, entity: HealthPlan) -> HealthPlan | None:
        async with self.database.session() as session:
            stmt = select(HealthPlan).filter_by(
                name=entity.name,
                address=entity.address,
                telephone=entity.telephone,
                responsible=entity.responsible,
                email=entity.email,
            )
            result = await session.execute(stmt)
            return result.scalars().first()