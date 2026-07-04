import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from infrastructure.database_context.database import Database
from infrastructure.models.case_study_submission import CaseStudySubmission


class CaseStudyRepository:
    def __init__(self, database: Database):
        self._db = database

    def _to_dict(self, c: CaseStudySubmission) -> dict:
        answers = c.answers or {}
        return {
            "id": c.id,
            "student_id": c.student_id,
            "student_name": c.student.name if c.student else answers.get("nomeAluno"),
            "submitted_by": c.submitted_by,
            "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None,
            "answers": answers,
        }

    async def list_all(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(CaseStudySubmission)
                .options(selectinload(CaseStudySubmission.student))
                .order_by(CaseStudySubmission.submitted_at.desc())
            )
            return [self._to_dict(c) for c in result.scalars().all()]

    async def get_by_id(self, case_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(CaseStudySubmission)
                .options(selectinload(CaseStudySubmission.student))
                .where(CaseStudySubmission.id == case_id)
            )
            c = result.scalar_one_or_none()
            return self._to_dict(c) if c else None

    async def create(self, data: dict) -> dict:
        async with self._db.session() as session:
            case = CaseStudySubmission(
                id=str(uuid.uuid4()),
                student_id=data.get("student_id") or None,
                submitted_by=data.get("submitted_by"),
                answers=data.get("answers", {}),
                submitted_at=datetime.utcnow(),
            )
            session.add(case)
            await session.commit()
            await session.refresh(case)
            return {
                "id": case.id,
                "student_id": case.student_id,
                "student_name": None,
                "submitted_by": case.submitted_by,
                "submitted_at": case.submitted_at.isoformat() if case.submitted_at else None,
                "answers": case.answers,
            }

    async def update(self, case_id: str, data: dict) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(CaseStudySubmission)
                .options(selectinload(CaseStudySubmission.student))
                .where(CaseStudySubmission.id == case_id)
            )
            case = result.scalar_one_or_none()
            if not case:
                return None
            if "answers" in data:
                case.answers = data["answers"]
            if "student_id" in data:
                case.student_id = data["student_id"] or None
            await session.commit()
            await session.refresh(case)
            return self._to_dict(case)

    async def delete(self, case_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(
                select(CaseStudySubmission).where(CaseStudySubmission.id == case_id)
            )
            case = result.scalar_one_or_none()
            if not case:
                return False
            await session.delete(case)
            await session.commit()
            return True
