from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from infrastructure.repositories.diary_question_repository import DiaryQuestionRepository, DiaryQuestionError

router = APIRouter(prefix="/diary-questions", tags=["Diary Questions"])

# Quem pode personalizar as perguntas de um aluno.
EDITOR_ROLES = ("admin", "secretaria", "coordenacao")


class QuestionItem(BaseModel):
    key: Optional[str] = None
    label: str = Field(max_length=300)


class QuestionsBody(BaseModel):
    questions: list[QuestionItem]


@router.get("/default")
@inject
async def get_default_questions(
    current_user: dict = Depends(get_current_user),
    repo: DiaryQuestionRepository = Depends(Provide[Container.diary_question_repository]),
):
    return {"questions": await repo.get_default()}


@router.get("/student/{student_id}")
@inject
async def get_student_questions(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    repo: DiaryQuestionRepository = Depends(Provide[Container.diary_question_repository]),
):
    return await repo.get_effective(student_id)


@router.put("/student/{student_id}")
@inject
async def replace_student_questions(
    student_id: str,
    body: QuestionsBody,
    current_user: dict = Depends(require_roles(*EDITOR_ROLES)),
    repo: DiaryQuestionRepository = Depends(Provide[Container.diary_question_repository]),
):
    try:
        return await repo.replace_for_student(student_id, [q.model_dump() for q in body.questions])
    except DiaryQuestionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/student/{student_id}")
@inject
async def reset_student_questions(
    student_id: str,
    current_user: dict = Depends(require_roles(*EDITOR_ROLES)),
    repo: DiaryQuestionRepository = Depends(Provide[Container.diary_question_repository]),
):
    return await repo.reset_student(student_id)
