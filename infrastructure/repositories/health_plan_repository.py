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
    
    async def list_all(self) -> list[HealthPlan]:
        async with self.database.session() as session:
            result = await session.execute(select(HealthPlan))
            return result.scalars().all()
    
    async def update(self, health_plan: HealthPlan) -> HealthPlan:
        try:
            async with self.database.session() as session:
                merged_health_plan = await session.merge(health_plan)
                await session.commit()
                await session.refresh(merged_health_plan)
                
                return merged_health_plan
        except Exception as e:
            raise e
    
    async def delete(self, health_plan: HealthPlan) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(health_plan)
                await session.commit()
        except Exception as e:
            raise e