from sqlalchemy import select, desc
from infrastructure.database_context.database import Database
from infrastructure.models.pei import PEI


class PEIRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, pei: PEI) -> PEI:
        """Adiciona um novo PEI ao banco de dados"""
        async with self.database.session() as session:
            session.add(pei)
            await session.commit()
            await session.refresh(pei)
            return pei

    async def get_by_id(self, pei_id: int) -> PEI | None:
        """Busca um PEI pelo ID"""
        async with self.database.session() as session:
            result = await session.execute(
                select(PEI).filter_by(id=pei_id)
            )
            return result.scalar_one_or_none()

    async def get_by_beneficiary(self, beneficiary_id: int, limit: int = 10):
        """Retorna todos os PEIs de um beneficiário"""
        async with self.database.session() as session:
            result = await session.execute(
                select(PEI)
                .filter_by(beneficiary_id=beneficiary_id)
                .order_by(desc(PEI.created_at))
                .limit(limit)
            )
            return result.scalars().all()

    async def get_latest_by_beneficiary(self, beneficiary_id: int) -> PEI | None:
        """Retorna o PEI mais recente de um beneficiário"""
        async with self.database.session() as session:
            result = await session.execute(
                select(PEI)
                .filter_by(beneficiary_id=beneficiary_id)
                .order_by(desc(PEI.created_at))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def update(self, pei: PEI) -> PEI:
        """Atualiza um PEI existente"""
        async with self.database.session() as session:
            await session.merge(pei)
            await session.commit()
            await session.refresh(pei)
            return pei

    async def delete(self, pei_id: int) -> bool:
        """Remove um PEI pelo ID"""
        try:
            async with self.database.session() as session:
                result = await session.execute(
                    select(PEI).filter_by(id=pei_id)
                )
                pei = result.scalar_one_or_none()

                if pei:
                    await session.delete(pei)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            raise e
