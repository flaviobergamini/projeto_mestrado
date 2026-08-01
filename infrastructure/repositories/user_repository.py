from typing import Optional
from sqlalchemy import select, delete, func
from infrastructure.database_context.database import Database
from infrastructure.models.user_profile import UserProfile
from infrastructure.models.municipality import Municipality
from infrastructure.models.school import School
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
        "created_at": u.created_at.isoformat() if u.created_at else None,
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
            # Check for soft-deleted record with same username
            existing_result = await session.execute(
                select(UserProfile).where(UserProfile.username == username, UserProfile.deleted == True)
            )
            existing = existing_result.scalars().first()
            if existing:
                existing.id = id
                existing.full_name = full_name
                existing.role = role
                existing.municipality_id = municipality_id
                existing.school_id = school_id
                existing.teacher_id = teacher_id
                existing.is_active = is_active
                existing.deleted = False
                await session.commit()
                await session.refresh(existing)
                return _to_dict(existing)

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
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            if not user:
                return None
            user.role = role
            await session.commit()
            await session.refresh(user)
            return _to_dict(user)

    async def update(self, user_id: str, full_name: Optional[str] = None, role: Optional[str] = None, is_active: Optional[bool] = None) -> dict | None:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            if not user:
                return None
            if full_name is not None:
                user.full_name = full_name
            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active
            await session.commit()
            await session.refresh(user)
            return _to_dict(user)

    async def delete(self, user_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.deleted = True
            await session.commit()
            return True

    async def get_by_username(self, username: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.username == username, UserProfile.deleted == False))
            user = result.scalars().first()
            return _to_dict(user) if user else None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            return _to_dict(user) if user else None

    async def get_all(self) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.deleted == False).order_by(UserProfile.username))
            return [_to_dict(u) for u in result.scalars().all()]

    async def list_by_role(self, role: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(UserProfile)
                .where(UserProfile.role == role, UserProfile.deleted == False)
                .order_by(UserProfile.full_name, UserProfile.username)
            )
            return [_to_dict(u) for u in result.scalars().all()]

    async def list_paginated(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        async with self.database.session() as session:
            total_result = await session.execute(select(func.count()).select_from(UserProfile).where(UserProfile.deleted == False))
            total = total_result.scalar() or 0

            result = await session.execute(
                select(UserProfile)
                .where(UserProfile.deleted == False)
                .order_by(UserProfile.username)
                .offset(offset)
                .limit(page_size)
            )
            items = [_to_dict(u) for u in result.scalars().all()]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }
