import uuid
from typing import Optional
from sqlalchemy import select, delete as sa_delete

from infrastructure.database_context.database import Database
from infrastructure.models.therapist_student_link import TherapistStudentLink
from infrastructure.models.student import Student
from infrastructure.models.user_profile import UserProfile


class TherapistStudentLinkRepository:
    def __init__(self, database: Database):
        self._db = database

    async def link(self, therapist_user_id: str, student_id: str) -> dict:
        async with self._db.session() as session:
            existing = await session.execute(
                select(TherapistStudentLink).where(
                    TherapistStudentLink.therapist_user_id == therapist_user_id,
                    TherapistStudentLink.student_id == student_id,
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                row.deleted = False
            else:
                row = TherapistStudentLink(
                    id=str(uuid.uuid4()),
                    therapist_user_id=therapist_user_id,
                    student_id=student_id,
                )
                session.add(row)
            await session.commit()
            return {"therapist_user_id": therapist_user_id, "student_id": student_id}

    async def unlink(self, therapist_user_id: str, student_id: str) -> None:
        async with self._db.session() as session:
            await session.execute(
                sa_delete(TherapistStudentLink).where(
                    TherapistStudentLink.therapist_user_id == therapist_user_id,
                    TherapistStudentLink.student_id == student_id,
                )
            )
            await session.commit()

    async def get_students_for_therapist(self, therapist_user_id: str) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Student)
                .join(TherapistStudentLink, TherapistStudentLink.student_id == Student.id)
                .where(
                    TherapistStudentLink.therapist_user_id == therapist_user_id,
                    TherapistStudentLink.deleted == False,
                    Student.deleted == False,
                )
            )
            return [{"id": s.id, "name": s.name, "grade": s.grade, "class_name": s.class_name} for s in result.scalars()]

    async def get_therapists_for_student(self, student_id: str) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(UserProfile)
                .join(TherapistStudentLink, TherapistStudentLink.therapist_user_id == UserProfile.id)
                .where(
                    TherapistStudentLink.student_id == student_id,
                    TherapistStudentLink.deleted == False,
                    UserProfile.deleted == False,
                )
            )
            return [{"id": u.id, "full_name": u.full_name, "username": u.username} for u in result.scalars()]

    async def is_linked(self, therapist_user_id: str, student_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(
                select(TherapistStudentLink).where(
                    TherapistStudentLink.therapist_user_id == therapist_user_id,
                    TherapistStudentLink.student_id == student_id,
                    TherapistStudentLink.deleted == False,
                )
            )
            return result.scalar_one_or_none() is not None

    async def set_students_for_therapist(self, therapist_user_id: str, student_ids: list[str]) -> None:
        async with self._db.session() as session:
            await session.execute(
                sa_delete(TherapistStudentLink).where(
                    TherapistStudentLink.therapist_user_id == therapist_user_id,
                )
            )
            for sid in student_ids:
                session.add(TherapistStudentLink(
                    id=str(uuid.uuid4()),
                    therapist_user_id=therapist_user_id,
                    student_id=sid,
                ))
            await session.commit()
