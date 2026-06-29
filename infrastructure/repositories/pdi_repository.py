import uuid
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from infrastructure.database_context.database import Database
from infrastructure.models.pdi import Pdi
from infrastructure.models.pdi_trimester_subject import PdiTrimesterSubject
from infrastructure.models.student import Student


class PdiRepository:
    def __init__(self, database: Database):
        self._db = database

    def _pdi_to_dict(self, pdi: Pdi, student: Optional[Student] = None) -> dict:
        s = student or pdi.student
        return {
            "id": pdi.id,
            "student_id": pdi.student_id,
            "student_name": s.name if s else None,
            "grade": s.grade if s else None,
            "class_name": pdi.class_name or (s.class_name if s else None),
            "diagnosis": pdi.diagnosis or (s.diagnosis if s else None),
            "teacher_name": pdi.teacher_name if hasattr(pdi, "teacher_name") else None,
            "birth_date": str(s.birth_date) if s and s.birth_date else None,
            "created_at": pdi.created_at.isoformat() if pdi.created_at else None,
            "updated_at": pdi.updated_at.isoformat() if pdi.updated_at else None,
        }

    def _subject_to_dict(self, ts: PdiTrimesterSubject) -> dict:
        return {
            "id": ts.id,
            "pdi_id": ts.pdi_id,
            "trimester": ts.trimester,
            "subject": ts.subject,
            "skills": ts.skills,
            "adaptations": ts.adaptations,
            "learnings": ts.learnings,
        }

    async def list_all(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Pdi).options(selectinload(Pdi.student)).order_by(Pdi.updated_at.desc())
            )
            pdis = result.scalars().all()
            return [self._pdi_to_dict(p) for p in pdis]

    async def get_by_id(self, pdi_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Pdi)
                .options(selectinload(Pdi.student), selectinload(Pdi.trimester_subjects))
                .where(Pdi.id == pdi_id)
            )
            pdi = result.scalar_one_or_none()
            if not pdi:
                return None
            data = self._pdi_to_dict(pdi)
            data["trimester_subjects"] = [self._subject_to_dict(ts) for ts in pdi.trimester_subjects]
            return data

    async def create(self, data: dict) -> dict:
        async with self._db.session() as session:
            student_result = await session.execute(
                select(Student).where(Student.id == data["student_id"])
            )
            student = student_result.scalar_one_or_none()

            pdi = Pdi(
                id=str(uuid.uuid4()),
                student_id=data["student_id"],
                class_name=data.get("class_name") or (student.class_name if student else None),
                diagnosis=data.get("diagnosis") or (student.diagnosis if student else None),
                teacher_name=data.get("teacher_name"),
            )
            session.add(pdi)
            await session.commit()
            await session.refresh(pdi)
            return self._pdi_to_dict(pdi, student)

    async def update(self, pdi_id: str, data: dict) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Pdi).options(selectinload(Pdi.student)).where(Pdi.id == pdi_id)
            )
            pdi = result.scalar_one_or_none()
            if not pdi:
                return None
            for field in ("class_name", "diagnosis", "teacher_name"):
                if field in data:
                    setattr(pdi, field, data[field])
            await session.commit()
            await session.refresh(pdi)
            return self._pdi_to_dict(pdi)

    async def delete(self, pdi_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(select(Pdi).where(Pdi.id == pdi_id))
            pdi = result.scalar_one_or_none()
            if not pdi:
                return False
            await session.delete(pdi)
            await session.commit()
            return True

    async def upsert_subjects(self, pdi_id: str, subjects: list[dict]) -> list[dict]:
        """Replace all trimester_subjects for a pdi with the provided list."""
        async with self._db.session() as session:
            await session.execute(
                delete(PdiTrimesterSubject).where(PdiTrimesterSubject.pdi_id == pdi_id)
            )
            rows = []
            for s in subjects:
                ts = PdiTrimesterSubject(
                    id=str(uuid.uuid4()),
                    pdi_id=pdi_id,
                    trimester=s["trimester"],
                    subject=s["subject"],
                    skills=s.get("skills"),
                    adaptations=s.get("adaptations"),
                    learnings=s.get("learnings"),
                )
                session.add(ts)
                rows.append(ts)
            await session.commit()
            return [self._subject_to_dict(r) for r in rows]
