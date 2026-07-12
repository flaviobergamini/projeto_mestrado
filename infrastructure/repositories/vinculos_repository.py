"""Repositório para gerenciar vínculos professor-aluno."""

import uuid
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from infrastructure.database_context.database import Database
from infrastructure.models.student import Student
from infrastructure.models.school import School
from infrastructure.models.teacher import Teacher
from infrastructure.models.teacher_student_link import TeacherStudentLink


class VinculosRepository:
    def __init__(self, database: Database):
        self._db = database

    async def list_students_with_links(
        self,
        page: int = 1,
        page_size: int = 20,
        name_filter: str | None = None,
    ) -> dict:
        async with self._db.session() as session:
            # Load all students with school + teacher_links → teacher
            result = await session.execute(
                select(Student)
                .options(
                    selectinload(Student.school),
                    selectinload(Student.teacher_links).selectinload(TeacherStudentLink.teacher),
                )
                .order_by(Student.name)
            )
            all_students = result.scalars().all()

        # Name filter in Python (field is encrypted — can't use SQL LIKE)
        if name_filter and name_filter.strip():
            needle = name_filter.strip().lower()
            all_students = [s for s in all_students if needle in (s.name or "").lower()]

        total = len(all_students)
        offset = (page - 1) * page_size
        page_students = all_students[offset: offset + page_size]

        items = []
        for s in page_students:
            teachers = [
                {"id": lnk.teacher.id, "name": lnk.teacher.name}
                for lnk in s.teacher_links
                if lnk.teacher
            ]
            items.append({
                "id": s.id,
                "name": s.name,
                "school_id": s.school_id,
                "school_name": s.school.name if s.school else None,
                "linked_teachers": teachers,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

    async def set_student_teachers(self, student_id: str, teacher_ids: list[str]) -> bool:
        async with self._db.session() as session:
            student = await session.get(Student, student_id)
            if not student:
                return False

            # Remove all existing links for this student
            await session.execute(
                delete(TeacherStudentLink).where(TeacherStudentLink.student_id == student_id)
            )

            # Insert new links
            for tid in teacher_ids:
                session.add(TeacherStudentLink(
                    id=str(uuid.uuid4()),
                    teacher_id=tid,
                    student_id=student_id,
                ))

            await session.commit()
        return True
