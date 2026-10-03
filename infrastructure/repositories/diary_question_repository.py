import uuid
from typing import Optional
from sqlalchemy import select, delete
from infrastructure.database_context.database import Database
from infrastructure.models.diary_question import DiaryQuestion
from core.constants.diary_questions import (
    DEFAULT_DIARY_QUESTIONS, BUILTIN_KEYS, DEFAULT_LABELS,
    MAX_QUESTIONS_PER_STUDENT, MAX_LABEL_LENGTH,
)


class DiaryQuestionError(ValueError):
    pass


def _row(q: DiaryQuestion) -> dict:
    return {
        "key": q.key,
        "label": q.label,
        "builtin": q.builtin,
        "default_label": DEFAULT_LABELS.get(q.key) if q.builtin else None,
    }


class DiaryQuestionRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def _rows(self, session, student_id: Optional[str]) -> list[DiaryQuestion]:
        cond = DiaryQuestion.student_id.is_(None) if student_id is None else DiaryQuestion.student_id == student_id
        result = await session.execute(select(DiaryQuestion).where(cond).order_by(DiaryQuestion.position))
        return list(result.scalars().all())

    async def get_default(self) -> list[dict]:
        async with self.database.session() as session:
            rows = await self._rows(session, None)
            if rows:
                return [_row(q) for q in rows]
        return [{"key": k, "label": label, "builtin": True, "default_label": label} for k, label in DEFAULT_DIARY_QUESTIONS]

    async def get_effective(self, student_id: str) -> dict:
        """Lista própria do aluno, se houver; senão o padrão."""
        async with self.database.session() as session:
            own = await self._rows(session, student_id)
        if own:
            return {"customized": True, "questions": [_row(q) for q in own]}
        return {"customized": False, "questions": await self.get_default()}

    async def replace_for_student(self, student_id: str, items: list[dict]) -> dict:
        """Substitui a lista do aluno (adicionar/remover/editar/reordenar de uma vez)."""
        if not items:
            raise DiaryQuestionError("O diário precisa ter ao menos uma pergunta. Use \"restaurar padrão\" para voltar às perguntas originais.")
        if len(items) > MAX_QUESTIONS_PER_STUDENT:
            raise DiaryQuestionError(f"Máximo de {MAX_QUESTIONS_PER_STUDENT} perguntas por aluno.")

        async with self.database.session() as session:
            existing = {q.key: q for q in await self._rows(session, student_id)}
            seen: set[str] = set()
            new_rows: list[DiaryQuestion] = []
            for position, item in enumerate(items):
                label = (item.get("label") or "").strip()
                if not label:
                    raise DiaryQuestionError("Toda pergunta precisa de um texto.")
                if len(label) > MAX_LABEL_LENGTH:
                    raise DiaryQuestionError(f"Cada pergunta pode ter no máximo {MAX_LABEL_LENGTH} caracteres.")
                key = item.get("key")
                if key in BUILTIN_KEYS:
                    builtin = True
                elif key and key in existing and not existing[key].builtin:
                    builtin = False
                else:
                    key, builtin = f"q_{uuid.uuid4().hex[:10]}", False
                if key in seen:
                    raise DiaryQuestionError("Pergunta duplicada na lista.")
                seen.add(key)
                new_rows.append(DiaryQuestion(
                    id=str(uuid.uuid4()), student_id=student_id, key=key,
                    label=label, position=position, builtin=builtin,
                ))
            await session.execute(delete(DiaryQuestion).where(DiaryQuestion.student_id == student_id))
            session.add_all(new_rows)
            await session.commit()
        return await self.get_effective(student_id)

    async def reset_student(self, student_id: str) -> dict:
        async with self.database.session() as session:
            await session.execute(delete(DiaryQuestion).where(DiaryQuestion.student_id == student_id))
            await session.commit()
        return await self.get_effective(student_id)
