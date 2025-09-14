import numpy as np
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.school import School


class SchoolRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, school: School) -> School:
        async with self.database.session() as session:
            session.add(school)
            await session.commit()
            await session.refresh(school)
            
            return school
        
    async def verify(self, entity: School) -> School | None:
        async with self.database.session() as session:
            stmt = select(School).filter_by(
                name=entity.name,
                address=entity.address,
                telephone=entity.telephone,
                email=entity.email,
                responsible=entity.responsible,
            )
            result = await session.execute(stmt)
            return result.scalars().first()
        
    async def list_all(self) -> list[School]:
        async with self.database.session() as session:
            result = await session.execute(select(School))
            return result.scalars().all()