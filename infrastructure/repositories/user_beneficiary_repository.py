from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.beneficiary import Beneficiary
from infrastructure.models.user_beneficiary import UserBeneficiary


class UserBeneficiaryRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, user_beneficiary: UserBeneficiary) -> UserBeneficiary:
        async with self.database.session() as session:
            session.add(user_beneficiary)
            await session.commit()
            await session.refresh(user_beneficiary)
            return user_beneficiary

    async def list_by_user(self, user_id: int) -> list[Beneficiary]:
        async with self.database.session() as session:
            stmt = (
                select(Beneficiary)
                .join(UserBeneficiary, UserBeneficiary.beneficiary_id == Beneficiary.id)
                .where(UserBeneficiary.user_id == user_id)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_by_user_and_beneficiary(self, user_id: int, beneficiary_id: int) -> UserBeneficiary | None:
        async with self.database.session() as session:
            stmt = select(UserBeneficiary).where(
                UserBeneficiary.user_id == user_id,
                UserBeneficiary.beneficiary_id == beneficiary_id,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def delete(self, user_beneficiary: UserBeneficiary) -> None:
        async with self.database.session() as session:
            await session.delete(user_beneficiary)
            await session.commit()
