from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.beneficiary_clinic import BeneficiaryClinic


class BeneficiaryClinicRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, beneficiary_clinic: BeneficiaryClinic) -> BeneficiaryClinic:
        async with self.database.session() as session:
            session.add(beneficiary_clinic)
            await session.commit()
            await session.refresh(beneficiary_clinic)

            return beneficiary_clinic

    async def verify(self, entity: BeneficiaryClinic) -> BeneficiaryClinic | None:
        async with self.database.session() as session:
            stmt = select(BeneficiaryClinic).filter_by(
                beneficiary_id=entity.beneficiary_id,
                clinic_id=entity.clinic_id,
                start_date=entity.start_date,
                end_date=entity.end_date,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[BeneficiaryClinic]:
        async with self.database.session() as session:
            result = await session.execute(select(BeneficiaryClinic))
            return result.scalars().all()

    async def get_by_id(self, beneficiary_clinic_id: int) -> BeneficiaryClinic | None:
        async with self.database.session() as session:
            stmt = select(BeneficiaryClinic).filter_by(id=beneficiary_clinic_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update(self, beneficiary_clinic: BeneficiaryClinic) -> BeneficiaryClinic:
        try:
            async with self.database.session() as session:
                merged_beneficiary_clinic = await session.merge(beneficiary_clinic)
                await session.commit()
                await session.refresh(merged_beneficiary_clinic)

                return merged_beneficiary_clinic
        except Exception as e:
            raise e

    async def delete(self, beneficiary_clinic: BeneficiaryClinic) -> None:
        try:
            async with self.database.session() as session:
                await session.delete(beneficiary_clinic)
                await session.commit()
        except Exception as e:
            raise e
