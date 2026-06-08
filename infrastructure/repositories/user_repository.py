from typing import Optional
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.user_profile import UserProfile
from core.interfaces.i_user_repository import IUserRepository


def _to_dict(u: UserProfile) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "municipality_id": u.municipality_id,
        "school_id": u.school_id,
        "teacher_id": u.teacher_id,
    }


class UserRepository(IUserRepository):
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(
        self,
        id: str,
        username: str,
        full_name: Optional[str],
        role: str,
        municipality_id: Optional[str],
        school_id: Optional[str],
        teacher_id: Optional[str],
        is_active: bool = True,
    ) -> dict:
        async with self.database.session() as session:
            user = UserProfile(
                id=id,
                username=username,
                full_name=full_name,
                role=role,
                municipality_id=municipality_id,
                school_id=school_id,
                teacher_id=teacher_id,
                is_active=is_active,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return _to_dict(user)

    async def update_role(self, user_id: str, role: str) -> dict:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id))
            user = result.scalars().first()
            if not user:
                return None
            user.role = role
            await session.commit()
            await session.refresh(user)
            return _to_dict(user)

    async def get_by_username(self, username: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.username == username))
            user = result.scalars().first()
            return _to_dict(user) if user else None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id))
            user = result.scalars().first()
            return _to_dict(user) if user else None

    async def get_all(self) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).order_by(UserProfile.username))
            return [_to_dict(u) for u in result.scalars().all()]
