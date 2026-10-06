"""Repositório de vínculos professor-aluno e da visão consolidada de relações."""

import uuid
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from core.interfaces.i_links_repository import ILinksRepository
from infrastructure.database_context.database import Database
from infrastructure.models.student import Student
from infrastructure.models.school import School
from infrastructure.models.teacher import Teacher
from infrastructure.models.teacher_student_link import TeacherStudentLink


class LinksRepository(ILinksRepository):
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
                .where(Student.deleted == False)
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
                if lnk.teacher and not lnk.deleted
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

            # Soft-delete all existing links for this student
            await session.execute(
                update(TeacherStudentLink).where(TeacherStudentLink.student_id == student_id).values(deleted=True)
            )

            # Insert new links (reactivate existing if deleted, else create new)
            for tid in teacher_ids:
                existing_result = await session.execute(
                    select(TeacherStudentLink).where(
                        TeacherStudentLink.teacher_id == tid,
                        TeacherStudentLink.student_id == student_id,
                    )
                )
                existing_link = existing_result.scalar_one_or_none()
                if existing_link:
                    existing_link.deleted = False
                else:
                    session.add(TeacherStudentLink(
                        id=str(uuid.uuid4()),
                        teacher_id=tid,
                        student_id=student_id,
                    ))

            await session.commit()
        return True

    async def relations(self) -> dict:
        """Visão consolidada (como o 'Relações de Pré-cadastro' da PoC): escolas por município,
        professores por escola/município (com alunos) e alunos por município/escola/professor."""
        from infrastructure.models.municipality import Municipality
        from infrastructure.models.teacher_school import TeacherSchool
        async with self._db.session() as session:
            munis = {m.id: m.name for m in (await session.execute(
                select(Municipality).where(Municipality.deleted == False))).scalars().all()}  # noqa: E712
            schools = (await session.execute(
                select(School).where(School.deleted == False))).scalars().all()  # noqa: E712
            teachers = (await session.execute(
                select(Teacher).where(Teacher.deleted == False))).scalars().all()  # noqa: E712
            students = (await session.execute(
                select(Student).where(Student.deleted == False))).scalars().all()  # noqa: E712
            t_schools = (await session.execute(select(TeacherSchool))).scalars().all()
            links = (await session.execute(
                select(TeacherStudentLink).where(TeacherStudentLink.deleted == False))).scalars().all()  # noqa: E712

        school_by_id = {s.id: s for s in schools}
        teacher_by_id = {t.id: t for t in teachers}
        student_by_id = {s.id: s for s in students}

        def school_ref(sid):
            s = school_by_id.get(sid)
            return {"id": sid, "name": s.name, "municipality_id": s.municipality_id,
                    "municipality_name": munis.get(s.municipality_id)} if s else None

        teacher_school_ids: dict[str, list[str]] = {}
        for ts in t_schools:
            teacher_school_ids.setdefault(ts.teacher_id, []).append(ts.school_id)
        for t in teachers:  # compatibilidade: school_id legado
            if t.school_id and t.school_id not in teacher_school_ids.setdefault(t.id, []):
                teacher_school_ids[t.id].append(t.school_id)

        t_students: dict[str, list[dict]] = {}
        s_teachers: dict[str, list[dict]] = {}
        for lk in links:
            t, s = teacher_by_id.get(lk.teacher_id), student_by_id.get(lk.student_id)
            if t and s:
                t_students.setdefault(t.id, []).append({"id": s.id, "name": s.name})
                s_teachers.setdefault(s.id, []).append({"id": t.id, "name": t.name})

        by_name = lambda x: (x["name"] or "").lower()  # noqa: E731
        return {
            "schools": sorted([{
                "id": s.id, "name": s.name, "municipality_id": s.municipality_id,
                "municipality_name": munis.get(s.municipality_id),
            } for s in schools], key=by_name),
            "teachers": sorted([{
                "id": t.id, "name": t.name,
                "schools": [r for r in (school_ref(i) for i in teacher_school_ids.get(t.id, [])) if r],
                "students": sorted(t_students.get(t.id, []), key=by_name),
            } for t in teachers], key=by_name),
            "students": sorted([{
                "id": s.id, "name": s.name, "school": school_ref(s.school_id),
                "teachers": sorted(s_teachers.get(s.id, []), key=by_name),
            } for s in students], key=by_name),
            "municipalities": sorted([{"id": i, "name": n} for i, n in munis.items()], key=by_name),
        }

    async def set_teacher_students(self, teacher_id: str, student_ids: list[str]) -> bool:
        async with self._db.session() as session:
            if not await session.get(Teacher, teacher_id):
                return False
            await session.execute(
                update(TeacherStudentLink).where(TeacherStudentLink.teacher_id == teacher_id).values(deleted=True)
            )
            for sid in student_ids:
                existing = (await session.execute(select(TeacherStudentLink).where(
                    TeacherStudentLink.teacher_id == teacher_id, TeacherStudentLink.student_id == sid,
                ))).scalar_one_or_none()
                if existing:
                    existing.deleted = False
                else:
                    session.add(TeacherStudentLink(id=str(uuid.uuid4()), teacher_id=teacher_id, student_id=sid))
            await session.commit()
        return True
