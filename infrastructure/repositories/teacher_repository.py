from core.interfaces.i_teacher_reader import ITeacherReader
import uuid
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from infrastructure.database_context.database import Database
from infrastructure.models.school import School
from infrastructure.models.teacher import Teacher
from infrastructure.models.teacher_school import TeacherSchool


def _requested_school_ids(data: dict) -> Optional[list[str]]:
    """Lista de escolas pedida no payload, sem duplicatas e na ordem recebida.
    None = payload não mexe nas escolas. `school_id` sozinho (chamadores antigos,
    ex.: ferramentas MCP) equivale a uma lista de um item."""
    if data.get("school_ids") is not None:
        ids = data["school_ids"]
    elif "school_id" in data:
        ids = [data["school_id"]] if data["school_id"] else []
    else:
        return None
    return list(dict.fromkeys(i for i in ids if i))


class TeacherRepository(ITeacherReader):
    def __init__(self, database: Database):
        self._db = database

    async def _schools_by_teacher(self, session, teacher_ids: list[str]) -> dict[str, list[dict]]:
        if not teacher_ids:
            return {}
        rows = await session.execute(
            select(TeacherSchool.teacher_id, School.id, School.name)
            .join(School, School.id == TeacherSchool.school_id)
            .where(TeacherSchool.teacher_id.in_(teacher_ids), School.deleted == False)
            .order_by(School.name)
        )
        out: dict[str, list[dict]] = {}
        for teacher_id, school_id, school_name in rows.all():
            out.setdefault(teacher_id, []).append({"id": school_id, "name": school_name})
        return out

    def _to_dict(self, t: Teacher, schools: list[dict]) -> dict:
        return {
            "id": t.id,
            "school_id": t.school_id,
            "school_name": t.school.name if t.school else None,
            "school_ids": [s["id"] for s in schools],
            "schools": schools,
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

    async def _replace_schools(self, session, teacher: Teacher, school_ids: list[str]) -> None:
        # A primeira escola da lista é a principal (teachers.school_id).
        teacher.school_id = school_ids[0] if school_ids else None
        await session.execute(delete(TeacherSchool).where(TeacherSchool.teacher_id == teacher.id))
        session.add_all(TeacherSchool(teacher_id=teacher.id, school_id=sid) for sid in school_ids)

    async def list_all(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Teacher).options(selectinload(Teacher.school)).where(Teacher.deleted == False).order_by(Teacher.name)
            )
            teachers = result.scalars().all()
            schools = await self._schools_by_teacher(session, [t.id for t in teachers])
            return [self._to_dict(t, schools.get(t.id, [])) for t in teachers]

    async def get_by_id(self, teacher_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Teacher).options(selectinload(Teacher.school)).where(Teacher.id == teacher_id, Teacher.deleted == False)
            )
            t = result.scalar_one_or_none()
            if not t:
                return None
            schools = await self._schools_by_teacher(session, [t.id])
            return self._to_dict(t, schools.get(t.id, []))

    async def create(self, data: dict) -> dict:
        async with self._db.session() as session:
            teacher = Teacher(
                id=str(uuid.uuid4()),
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
            await session.flush()
            await self._replace_schools(session, teacher, _requested_school_ids(data) or [])
            await session.commit()

        return await self.get_by_id(teacher.id)

    async def update(self, teacher_id: str, data: dict) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Teacher).where(Teacher.id == teacher_id, Teacher.deleted == False)
            )
            teacher = result.scalar_one_or_none()
            if not teacher:
                return None

            for field in ("name", "specialization", "email", "phone", "notes",
                          "birth_year", "gender", "teacher_role"):
                if field in data:
                    setattr(teacher, field, data[field])

            school_ids = _requested_school_ids(data)
            if school_ids is not None:
                await self._replace_schools(session, teacher, school_ids)

            await session.commit()

        return await self.get_by_id(teacher_id)

    async def delete(self, teacher_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(select(Teacher).where(Teacher.id == teacher_id, Teacher.deleted == False))
            teacher = result.scalar_one_or_none()
            if not teacher:
                return False
            teacher.deleted = True
            await session.commit()
            return True
