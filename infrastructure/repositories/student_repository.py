import uuid
import json
from datetime import date
from typing import Optional
from sqlalchemy import select, func
from infrastructure.database_context.database import Database
from infrastructure.models.student import Student
from infrastructure.models.school import School
from infrastructure.services.anonymization_service import anon_student


def _build_anonymized_data(student_id: str, school_id: str | None, age: str | None,
                            grade: str | None, class_name: str | None, diagnosis: str | None) -> str:
    return json.dumps(anon_student({
        "id": student_id, "school_id": school_id,
        "age": age, "grade": grade, "class_name": class_name, "diagnosis": diagnosis,
    }), ensure_ascii=False)


def _to_dict(s: Student, school_name: Optional[str] = None) -> dict:
    guardians = []
    if s.guardians:
        try:
            guardians = json.loads(s.guardians)
        except Exception:
            guardians = [s.guardians] if s.guardians else []
    return {
        "id": s.id,
        "school_id": s.school_id,
        "school_name": school_name,
        "name": s.name,
        "birth_date": s.birth_date.isoformat() if s.birth_date else None,
        "age": s.age,
        "grade": s.grade,
        "class_name": s.class_name,
        "guardians": guardians,
        "diagnosis": s.diagnosis,
        "notes": s.notes,
        "autism_support_level": s.autism_support_level,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


class StudentRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def list_all(self, school_id: Optional[str] = None) -> list[dict]:
        async with self.database.session() as session:
            stmt = (
                select(Student, School.name.label("school_name"))
                .outerjoin(School, Student.school_id == School.id)
                .where(Student.deleted == False)
                .order_by(Student.name)
            )
            if school_id:
                stmt = stmt.where(Student.school_id == school_id)
            result = await session.execute(stmt)
            rows = result.all()
            return [_to_dict(row.Student, row.school_name) for row in rows]

    async def get_by_id(self, student_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(Student, School.name.label("school_name"))
                .outerjoin(School, Student.school_id == School.id)
                .where(Student.id == student_id, Student.deleted == False)
            )
            row = result.first()
            if not row:
                return None
            return _to_dict(row.Student, row.school_name)

    async def create(self, data: dict) -> dict:
        async with self.database.session() as session:
            guardians = data.get("guardians", [])
            sid = str(uuid.uuid4())
            student = Student(
                id=sid,
                school_id=data.get("school_id"),
                name=data["name"],
                birth_date=date.fromisoformat(data["birth_date"]) if data.get("birth_date") else None,
                age=data.get("age"),
                grade=data.get("grade"),
                class_name=data.get("class_name"),
                guardians=json.dumps(guardians, ensure_ascii=False) if guardians else None,
                diagnosis=data.get("diagnosis"),
                notes=data.get("notes"),
                autism_support_level=data.get("autism_support_level"),
                anonymized_data=_build_anonymized_data(
                    sid, data.get("school_id"), data.get("age"),
                    data.get("grade"), data.get("class_name"), data.get("diagnosis"),
                ),
            )
            session.add(student)
            await session.commit()
            await session.refresh(student)
            return _to_dict(student)

    async def update(self, student_id: str, data: dict) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(Student).where(Student.id == student_id))
            student = result.scalars().first()
            if not student:
                return None
            if "name" in data:
                student.name = data["name"]
            if "school_id" in data:
                student.school_id = data["school_id"]
            if "birth_date" in data:
                student.birth_date = date.fromisoformat(data["birth_date"]) if data["birth_date"] else None
            if "age" in data:
                student.age = data["age"]
            if "grade" in data:
                student.grade = data["grade"]
            if "class_name" in data:
                student.class_name = data["class_name"]
            if "guardians" in data:
                guardians = data["guardians"]
                student.guardians = json.dumps(guardians, ensure_ascii=False) if guardians else None
            if "diagnosis" in data:
                student.diagnosis = data["diagnosis"]
            if "notes" in data:
                student.notes = data["notes"]
            if "autism_support_level" in data:
                student.autism_support_level = data["autism_support_level"]
            # Refresh anonymized_data whenever non-PII fields change
            student.anonymized_data = _build_anonymized_data(
                student.id, student.school_id, student.age,
                student.grade, student.class_name, student.diagnosis,
            )
            await session.commit()
            await session.refresh(student)
            # fetch school name
            school_name = None
            if student.school_id:
                school_result = await session.execute(
                    select(School.name).where(School.id == student.school_id)
                )
                school_name = school_result.scalar_one_or_none()
            return _to_dict(student, school_name)

    async def delete(self, student_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(select(Student).where(Student.id == student_id))
            student = result.scalars().first()
            if not student:
                return False
            student.deleted = True
            await session.commit()
            return True
