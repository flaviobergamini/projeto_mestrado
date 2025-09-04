import numpy as np
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.beneficiary import Beneficiary


class BeneficiaryRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, beneficiary: Beneficiary) -> Beneficiary:
        async with self.database.session() as session:
            session.add(beneficiary)
            await session.commit()
            await session.refresh(beneficiary)
            
            return beneficiary
        
    async def get_by_id(self, id: int) -> Beneficiary | None:
        async with self.database.session() as session:
            result = await session.execute(select(Beneficiary).where(Beneficiary.id == id))
            return result.scalars().first()