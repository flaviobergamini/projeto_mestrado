import uuid
from typing import Optional
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.skill import Skill


def _to_dict(s: Skill) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "prompt": s.prompt,
        "created_by": s.created_by,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


class SkillRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def list_all(self) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(Skill).where(Skill.deleted == False).order_by(Skill.title)
            )
            return [_to_dict(s) for s in result.scalars().all()]

    async def get_by_id(self, skill_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(Skill).where(Skill.id == skill_id, Skill.deleted == False)
            )
            skill = result.scalars().first()
            return _to_dict(skill) if skill else None

    async def create(self, data: dict) -> dict:
        async with self.database.session() as session:
            skill = Skill(
                id=str(uuid.uuid4()),
                title=data["title"],
                description=data.get("description"),
                prompt=data["prompt"],
                created_by=data.get("created_by"),
            )
            session.add(skill)
            await session.commit()
            await session.refresh(skill)
            return _to_dict(skill)

    async def update(self, skill_id: str, data: dict) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(Skill).where(Skill.id == skill_id, Skill.deleted == False)
            )
            skill = result.scalars().first()
            if not skill:
                return None
            for field in ("title", "description", "prompt"):
                if field in data:
                    setattr(skill, field, data[field])
            await session.commit()
            await session.refresh(skill)
            return _to_dict(skill)

    async def delete(self, skill_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(
                select(Skill).where(Skill.id == skill_id, Skill.deleted == False)
            )
            skill = result.scalars().first()
            if not skill:
                return False
            skill.deleted = True
            await session.commit()
            return True
