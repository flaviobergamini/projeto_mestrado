import uuid
from typing import Optional
from sqlalchemy import select, delete as sa_delete

from infrastructure.database_context.database import Database
from infrastructure.models.parent_student_link import ParentStudentLink
from infrastructure.models.student import Student
from infrastructure.models.user_profile import UserProfile


class ParentStudentLinkRepository:
    def __init__(self, database: Database):
        self._db = database

    async def link(self, parent_user_id: str, student_id: str) -> dict:
        async with self._db.session() as session:
            existing = await session.execute(
                select(ParentStudentLink).where(
                    ParentStudentLink.parent_user_id == parent_user_id,
                    ParentStudentLink.student_id == student_id,
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                row.deleted = False
            else:
                row = ParentStudentLink(
                    id=str(uuid.uuid4()),
                    parent_user_id=parent_user_id,
                    student_id=student_id,
                )
                session.add(row)
            await session.commit()
            return {"parent_user_id": parent_user_id, "student_id": student_id}

    async def unlink(self, parent_user_id: str, student_id: str) -> None:
        async with self._db.session() as session:
            await session.execute(
                sa_delete(ParentStudentLink).where(
                    ParentStudentLink.parent_user_id == parent_user_id,
                    ParentStudentLink.student_id == student_id,
                )
            )
            await session.commit()

    async def get_students_for_parent(self, parent_user_id: str) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Student)
                .join(ParentStudentLink, ParentStudentLink.student_id == Student.id)
                .where(
                    ParentStudentLink.parent_user_id == parent_user_id,
                    ParentStudentLink.deleted == False,
                    Student.deleted == False,
                )
            )
            return [{"id": s.id, "name": s.name, "grade": s.grade, "class_name": s.class_name} for s in result.scalars()]

    async def get_parents_for_student(self, student_id: str) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(UserProfile)
                .join(ParentStudentLink, ParentStudentLink.parent_user_id == UserProfile.id)
                .where(
                    ParentStudentLink.student_id == student_id,
                    ParentStudentLink.deleted == False,
                    UserProfile.deleted == False,
                )
            )
            return [{"id": u.id, "full_name": u.full_name, "username": u.username} for u in result.scalars()]

    async def is_linked(self, parent_user_id: str, student_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(
                select(ParentStudentLink).where(
                    ParentStudentLink.parent_user_id == parent_user_id,
                    ParentStudentLink.student_id == student_id,
                    ParentStudentLink.deleted == False,
                )
            )
            return result.scalar_one_or_none() is not None

    async def set_students_for_parent(self, parent_user_id: str, student_ids: list[str]) -> None:
        async with self._db.session() as session:
            await session.execute(
                sa_delete(ParentStudentLink).where(
                    ParentStudentLink.parent_user_id == parent_user_id,
                )
            )
            for sid in student_ids:
                session.add(ParentStudentLink(
                    id=str(uuid.uuid4()),
                    parent_user_id=parent_user_id,
                    student_id=sid,
                ))
            await session.commit()
