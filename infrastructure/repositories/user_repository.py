from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.users import User

class UserRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, user: User) -> User:
        async with self.database.session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)

            return user

    async def update(self, user: User) -> User:
        async with self.database.session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)

            return user

    async def get_by_email(self, email: str) -> User | None:
        async with self.database.session() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalars().first()

    async def get_by_id(self, user_id: int) -> User | None:
        async with self.database.session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalars().first()

    async def get_by_verification_token(self, token: str) -> User | None:
        async with self.database.session() as session:
            result = await session.execute(select(User).where(User.verification_token == token))
            return result.scalars().first()

    async def get_by_reset_token(self, token: str) -> User | None:
        async with self.database.session() as session:
            result = await session.execute(select(User).where(User.reset_token == token))
            return result.scalars().first()