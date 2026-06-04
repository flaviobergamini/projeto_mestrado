from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.user_profile import UserProfile


class UserRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, user: UserProfile) -> UserProfile:
        async with self.database.session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def update(self, user: UserProfile) -> UserProfile:
        async with self.database.session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_by_username(self, username: str) -> UserProfile | None:
        async with self.database.session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.username == username)
            )
            return result.scalars().first()

    async def get_by_id(self, user_id: str) -> UserProfile | None:
        async with self.database.session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.id == user_id)
            )
            return result.scalars().first()

    async def get_all(self) -> list[UserProfile]:
        async with self.database.session() as session:
            result = await session.execute(
                select(UserProfile).order_by(UserProfile.username)
            )
            return list(result.scalars().all())
