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
        
    async def verify(self, entity: Beneficiary) -> Beneficiary | None:
        async with self.database.session() as session:
            stmt = select(Beneficiary).filter_by(
                name=entity.name,
                date_of_birth=entity.date_of_birth,
                diagnosis=entity.diagnosis,
                main_responsible=entity.main_responsible,
                responsible_contact=entity.responsible_contact,
                entry_date=entity.entry_date,
                exit_date=entity.exit_date,
                status=entity.status,
                school_id=entity.school_id,
                healthplan_id=entity.healthplan_id
            )
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def list_all(self) -> list[Beneficiary]:
        async with self.database.session() as session:
            result = await session.execute(select(Beneficiary))
            return result.scalars().all()
    
    async def get_by_id(self, id: int) -> Beneficiary | None:
        async with self.database.session() as session:
            result = await session.execute(select(Beneficiary).where(Beneficiary.id == id))
            return result.scalars().first()
    
    async def update(self, beneficiary: Beneficiary) -> Beneficiary:
        try:
            async with self.database.session() as session:
                merged_beneficiary = await session.merge(beneficiary)
                await session.commit()
                await session.refresh(merged_beneficiary)
                
                return merged_beneficiary
        except Exception as e:
            raise e
    
    async def delete(self, beneficiary: Beneficiary) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(beneficiary)
                await session.commit()
        except Exception as e:
            raise e