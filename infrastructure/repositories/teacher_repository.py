import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from infrastructure.database_context.database import Database
from infrastructure.models.teacher import Teacher


class TeacherRepository:
    def __init__(self, database: Database):
        self._db = database

    def _to_dict(self, t: Teacher) -> dict:
        return {
            "id": t.id,
            "school_id": t.school_id,
            "school_name": t.school.name if t.school else None,
            "name": t.name,
            "specialization": t.specialization,
            "email": t.email,
            "phone": t.phone,
            "notes": t.notes,
            "birth_year": t.birth_year,
            "gender": t.gender,
            "teacher_role": t.teacher_role,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }

    async def list_all(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Teacher).options(selectinload(Teacher.school)).where(Teacher.deleted == False).order_by(Teacher.name)
            )

            return [self._to_dict(t) for t in result.scalars().all()]

    async def get_by_id(self, teacher_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Teacher).options(selectinload(Teacher.school)).where(Teacher.id == teacher_id, Teacher.deleted == False)
            )

            t = result.scalar_one_or_none()

            return self._to_dict(t) if t else None

    async def create(self, data: dict) -> dict:
        async with self._db.session() as session:
            teacher = Teacher(
                id=str(uuid.uuid4()),
                school_id=data.get("school_id") or None,
                name=data["name"],
                specialization=data.get("specialization"),
                email=data.get("email"),
                phone=data.get("phone"),
                notes=data.get("notes"),
                birth_year=data.get("birth_year"),
                gender=data.get("gender"),
                teacher_role=data.get("teacher_role"),
            )

            session.add(teacher)

            await session.commit()

            await session.refresh(teacher)

            return {
                "id": teacher.id,
                "school_id": teacher.school_id,
                "school_name": None,
                "name": teacher.name,
                "specialization": teacher.specialization,
                "email": teacher.email,
                "phone": teacher.phone,
                "notes": teacher.notes,
                "birth_year": teacher.birth_year,
                "gender": teacher.gender,
                "teacher_role": teacher.teacher_role,
                "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
                "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
            }

    async def update(self, teacher_id: str, data: dict) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Teacher).options(selectinload(Teacher.school)).where(Teacher.id == teacher_id, Teacher.deleted == False)
            )

            teacher = result.scalar_one_or_none()

            if not teacher:
                return None
            
            for field in ("name", "school_id", "specialization", "email", "phone", "notes",
                          "birth_year", "gender", "teacher_role"):
                if field in data:
                    setattr(teacher, field, data[field] or None if field == "school_id" else data[field])

            await session.commit()

            await session.refresh(teacher)

            return self._to_dict(teacher)

    async def delete(self, teacher_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(select(Teacher).where(Teacher.id == teacher_id, Teacher.deleted == False))

            teacher = result.scalar_one_or_none()

            if not teacher:
                return False

            teacher.deleted = True

            await session.commit()

            return True
