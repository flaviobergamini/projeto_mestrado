import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, Any
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.case_study_repository import CaseStudyRepository
from infrastructure.repositories.case_study_draft_repository import CaseStudyDraftRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.services.rag_service import RagService

router = APIRouter(prefix="/case-studies", tags=["Case Studies"])


class CaseStudyCreate(BaseModel):
    student_id: Optional[str] = None
    answers: dict[str, Any] = {}


class CaseStudyUpdate(BaseModel):
    student_id: Optional[str] = None
    answers: Optional[dict[str, Any]] = None


@router.get("")
@inject
async def list_case_studies(
    current_user: dict = Depends(get_current_user),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    return await repo.list_all()


@router.get("/{case_id}")
@inject
async def get_case_study(
    case_id: str,
    current_user: dict = Depends(get_current_user),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    case = await repo.get_by_id(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudo de caso não encontrado")
    return case


async def _trigger_case_embedding(rag: RagService, student_repo: StudentRepository, case: dict) -> None:
    """Fire-and-forget: embed case study (anonymised — no student name sent to Gemini)."""
    try:
        await rag.embed_case_study(case)
    except Exception:
        pass


class DraftUpsert(BaseModel):
    student_id: str
    answers: dict[str, Any] = {}
    case_study_id: Optional[str] = None


# ── Draft endpoints (must be before /{case_id} to avoid route conflict) ────────

@router.get("/draft")
@inject
async def get_draft(
    student_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    draft_repo: CaseStudyDraftRepository = Depends(Provide[Container.case_study_draft_repository]),
):
    """Return the in-progress draft for the current user + student, or null."""
    draft = await draft_repo.get(current_user["user_id"], student_id)
    return draft  # None serialises to null in JSON


@router.put("/draft", status_code=status.HTTP_200_OK)
@inject
async def upsert_draft(
    body: DraftUpsert,
    current_user: dict = Depends(get_current_user),
    draft_repo: CaseStudyDraftRepository = Depends(Provide[Container.case_study_draft_repository]),
):
    """Create or update the draft for the current user + student."""
    return await draft_repo.upsert(
        user_id=current_user["user_id"],
        student_id=body.student_id,
        answers=body.answers,
        case_study_id=body.case_study_id,
    )


@router.delete("/draft", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_draft(
    student_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    draft_repo: CaseStudyDraftRepository = Depends(Provide[Container.case_study_draft_repository]),
):
    """Delete the draft after the case study is finalised."""
    await draft_repo.delete(current_user["user_id"], student_id)


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_case_study(
    body: CaseStudyCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
    draft_repo: CaseStudyDraftRepository = Depends(Provide[Container.case_study_draft_repository]),
):
    data = body.model_dump()
    data["submitted_by"] = current_user.get("full_name") or current_user.get("username", "")
    case = await repo.create(data)
    asyncio.create_task(_trigger_case_embedding(rag, student_repo, case))
    # Clean up draft on successful save
    if data.get("student_id"):
        await draft_repo.delete(current_user["user_id"], data["student_id"])
    return case


@router.put("/{case_id}")
@inject
async def update_case_study(
    case_id: str,
    body: CaseStudyUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
    draft_repo: CaseStudyDraftRepository = Depends(Provide[Container.case_study_draft_repository]),
):
    updated = await repo.update(case_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudo de caso não encontrado")
    asyncio.create_task(_trigger_case_embedding(rag, student_repo, updated))
    # Clean up draft on successful save
    if updated.get("student_id"):
        await draft_repo.delete(current_user["user_id"], updated["student_id"])
    return updated


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_case_study(
    case_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: CaseStudyRepository = Depends(Provide[Container.case_study_repository]),
):
    deleted = await repo.delete(case_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudo de caso não encontrado")
