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
    
    async def get_by_email(self, email: str) -> User | None:
        async with self.database.session() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalars().first()