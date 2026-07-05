import uuid
from datetime import date
from typing import Optional
from sqlalchemy import select, func, delete
from infrastructure.database_context.database import Database
from infrastructure.models.diary_entry import DiaryEntry
from infrastructure.models.student import Student
from infrastructure.models.teacher_student_link import TeacherStudentLink
from infrastructure.models.teacher import Teacher


def _to_dict(e: DiaryEntry) -> dict:
    return {
        "id": e.id,
        "student_id": e.student_id,
        "diary_date": e.diary_date.isoformat() if e.diary_date else None,
        "teacher_attention": e.teacher_attention,
        "followed_agreements": e.followed_agreements,
        "activity_interest": e.activity_interest,
        "had_lunch": e.had_lunch,
        "participated_in_play": e.participated_in_play,
        "completed_activities": e.completed_activities,
        "bathroom_use": e.bathroom_use,
        "open_observation": e.open_observation,
        "absence_reason": e.absence_reason,
        "teacher_name": e.teacher_name,
        "presence": e.presence,
        "status": e.status,
        "source": e.source,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }


class DiaryRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def list_students_with_diary(self) -> list[dict]:
        """Returns one summary entry per student that has at least one diary entry."""
        async with self.database.session() as session:
            # Aggregate per student
            stmt = (
                select(
                    DiaryEntry.student_id,
                    Student.name.label("student_name"),
                    func.max(DiaryEntry.diary_date).label("last_entry"),
                    func.count(DiaryEntry.id).label("total_entries"),
                )
                .outerjoin(Student, DiaryEntry.student_id == Student.id)
                .group_by(DiaryEntry.student_id, Student.name)
                .order_by(Student.name)
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [
                {
                    "student_id": row.student_id,
                    "student_name": row.student_name or row.student_id,
                    "last_entry": row.last_entry.isoformat() if row.last_entry else None,
                    "total_entries": row.total_entries,
                }
                for row in rows
            ]

    async def list_by_student(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(DiaryEntry)
                .where(DiaryEntry.student_id == student_id)
                .order_by(DiaryEntry.diary_date.desc())
            )
            return [_to_dict(e) for e in result.scalars().all()]

    async def get_by_id(self, entry_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(DiaryEntry).where(DiaryEntry.id == entry_id))
            e = result.scalars().first()
            return _to_dict(e) if e else None

    async def create(self, data: dict) -> dict:
        async with self.database.session() as session:
            entry = DiaryEntry(
                id=str(uuid.uuid4()),
                student_id=data.get("student_id"),
                diary_date=date.fromisoformat(data["diary_date"]) if data.get("diary_date") else None,
                teacher_attention=data.get("teacher_attention"),
                followed_agreements=data.get("followed_agreements"),
                activity_interest=data.get("activity_interest"),
                had_lunch=data.get("had_lunch"),
                participated_in_play=data.get("participated_in_play"),
                completed_activities=data.get("completed_activities"),
                bathroom_use=data.get("bathroom_use"),
                open_observation=data.get("open_observation"),
                absence_reason=data.get("absence_reason"),
                teacher_name=data.get("teacher_name"),
                presence=data.get("presence", "Presente"),
                status="active",
                source="manual",
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return _to_dict(entry)

    async def update(self, entry_id: str, data: dict) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(DiaryEntry).where(DiaryEntry.id == entry_id))
            entry = result.scalars().first()
            if not entry:
                return None
            for field in [
                "diary_date", "teacher_attention", "followed_agreements", "activity_interest",
                "had_lunch", "participated_in_play", "completed_activities", "bathroom_use",
                "open_observation", "absence_reason", "teacher_name", "presence",
            ]:
                if field in data:
                    value = data[field]
                    if field == "diary_date" and value:
                        value = date.fromisoformat(value)
                    setattr(entry, field, value)
            await session.commit()
            await session.refresh(entry)
            return _to_dict(entry)

    async def delete(self, entry_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(select(DiaryEntry).where(DiaryEntry.id == entry_id))
            entry = result.scalars().first()
            if not entry:
                return False
            await session.delete(entry)
            await session.commit()
            return True

    async def get_linked_teachers(self, student_id: str) -> list[str]:
        """Returns list of teacher names linked to the given student."""
        async with self.database.session() as session:
            stmt = (
                select(Teacher.name)
                .join(TeacherStudentLink, Teacher.id == TeacherStudentLink.teacher_id)
                .where(TeacherStudentLink.student_id == student_id)
                .order_by(Teacher.name)
            )
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    async def delete_all_for_student(self, student_id: str) -> int:
        async with self.database.session() as session:
            result = await session.execute(
                delete(DiaryEntry).where(DiaryEntry.student_id == student_id)
            )
            await session.commit()
            return result.rowcount
