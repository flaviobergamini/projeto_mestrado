import json
import uuid
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from infrastructure.database_context.database import Database
from infrastructure.models.case_study_draft import CaseStudyDraft


class CaseStudyDraftRepository:
    def __init__(self, database: Database):
        self._db = database

    async def upsert(
        self,
        user_id: str,
        student_id: str,
        answers: dict,
        case_study_id: Optional[str] = None,
    ) -> dict:
        """Insert or update the draft for this user+student pair."""
        async with self._db.session() as session:
            result = await session.execute(
                select(CaseStudyDraft).where(
                    CaseStudyDraft.user_id == user_id,
                    CaseStudyDraft.student_id == student_id,
                )
            )
            row = result.scalar_one_or_none()

            if row:
                row.answers = json.dumps(answers, ensure_ascii=False)
                if case_study_id is not None:
                    row.case_study_id = case_study_id
            else:
                row = CaseStudyDraft(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    student_id=student_id,
                    case_study_id=case_study_id,
                    answers=json.dumps(answers, ensure_ascii=False),
                )
                session.add(row)

            await session.commit()
            await session.refresh(row)
            return self._to_dict(row)

    async def get(self, user_id: str, student_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(CaseStudyDraft).where(
                    CaseStudyDraft.user_id == user_id,
                    CaseStudyDraft.student_id == student_id,
                )
            )
            row = result.scalar_one_or_none()
            return self._to_dict(row) if row else None

    async def delete(self, user_id: str, student_id: str) -> None:
        async with self._db.session() as session:
            await session.execute(
                delete(CaseStudyDraft).where(
                    CaseStudyDraft.user_id == user_id,
                    CaseStudyDraft.student_id == student_id,
                )
            )
            await session.commit()

    def _to_dict(self, row: CaseStudyDraft) -> dict:
        answers = {}
        try:
            answers = json.loads(row.answers)
        except Exception:
            pass
        return {
            "id": row.id,
            "user_id": row.user_id,
            "student_id": row.student_id,
            "case_study_id": row.case_study_id,
            "answers": answers,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
