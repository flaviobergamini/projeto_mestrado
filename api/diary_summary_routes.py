import asyncio
from datetime import date as _date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from dependency_injector.wiring import inject, Provide
from pydantic import BaseModel
from typing import Optional

from core.kernel.container import Container
from api.dependencies import get_current_user
from core.permissions.roles import CAN_GENERATE_DIARY_SUMMARY, CAN_VIEW_DIARY_SUMMARY, ADMIN, PARENT
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.diary_summary_repository import DiarySummaryRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.repositories.parent_student_link_repository import ParentStudentLinkRepository
from infrastructure.services.gemini_service import GeminiService

router = APIRouter(prefix="/diary-summary", tags=["Resumo Diário"])


class EntryRef(BaseModel):
    type: str  # "school" | "family"
    id: str


class DiarySummaryChatRequest(BaseModel):
    student_id: str
    session_id: Optional[str] = None
    message: str
    entry_ids: list[EntryRef]
    instruction_prompt: str


class DiarySummaryChatResponse(BaseModel):
    session_id: str
    answer: str
    message_index: int


class SourceEntryRef(BaseModel):
    type: str
    id: str
    date: Optional[str] = None


class CreateDiarySummaryRequest(BaseModel):
    student_id: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    summary_text: str
    source_entries: list[SourceEntryRef] = []


def _require_generate(current_user: dict):
    if current_user.get("role", "") not in CAN_GENERATE_DIARY_SUMMARY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")


def _require_view(current_user: dict):
    if current_user.get("role", "") not in CAN_VIEW_DIARY_SUMMARY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")


@router.get("/students")
@inject
async def list_students_with_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    """Lista alunos com ao menos uma entrada de diário (escolar ou familiar) no período."""
    _require_generate(current_user)

    date_from = _date.fromisoformat(start_date) if start_date else None
    date_to = _date.fromisoformat(end_date) if end_date else None

    school_counts = await diary_repo.count_entries_by_student_in_range("school", date_from, date_to)
    family_counts = await diary_repo.count_entries_by_student_in_range("family", date_from, date_to)

    student_ids = set(school_counts) | set(family_counts)
    if not student_ids:
        return []

    all_students = await student_repo.list_all()
    students_by_id = {s["id"]: s for s in all_students if s["id"] in student_ids}

    result = []
    for sid in student_ids:
        s = students_by_id.get(sid)
        if not s:
            continue
        result.append({
            "id": s["id"],
            "name": s["name"],
            "school_name": s.get("school_name"),
            "school_entries_count": school_counts.get(sid, 0),
            "family_entries_count": family_counts.get(sid, 0),
        })

    result.sort(key=lambda r: r["name"] or "")
    return result


def _entry_preview(entry: dict) -> str:
    text = entry.get("open_observation") or ""
    text = text.strip()
    if not text:
        return "Sem observações"
    return text[:160]


def _entry_author_name(entry: dict) -> Optional[str]:
    # DiaryEntry uses teacher_name for both school and family sources
    # (family entries store the responsible parent/guardian's name there too).
    return entry.get("teacher_name")


@router.get("/entries")
@inject
async def list_entries_for_selection(
    student_id: str = Query(...),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    """Lista entradas de diário (escolar + familiar) de um aluno no período, para seleção via checkbox."""
    _require_generate(current_user)

    date_from = _date.fromisoformat(start_date) if start_date else None
    date_to = _date.fromisoformat(end_date) if end_date else None

    school_entries = await diary_repo.list_by_student(student_id, source="school", date_from=date_from, date_to=date_to)
    family_entries = await diary_repo.list_by_student(student_id, source="family", date_from=date_from, date_to=date_to)

    result = []
    for e in school_entries:
        result.append({
            "type": "school",
            "id": e["id"],
            "date": e.get("diary_date"),
            "preview": _entry_preview(e),
            "author_name": _entry_author_name(e),
        })
    for e in family_entries:
        result.append({
            "type": "family",
            "id": e["id"],
            "date": e.get("diary_date"),
            "preview": _entry_preview(e),
            "author_name": _entry_author_name(e),
        })

    result.sort(key=lambda r: r["date"] or "", reverse=True)
    return result


def _format_entries_block(entries: list[dict]) -> str:
    lines = ["=== REGISTROS DE DIÁRIO SELECIONADOS ==="]
    for e in entries:
        label = "Diário Escolar" if e.get("source") == "school" else "Diário Familiar"
        lines.append(f"- [{label}] Data: {e.get('diary_date')}")
        if e.get("open_observation"):
            lines.append(f"  Observação: {e['open_observation']}")
        indicadores = []
        for field, label_pt in [
            ("teacher_attention", "atenção"),
            ("activity_interest", "interesse nas atividades"),
            ("participated_in_play", "participou de brincadeiras"),
            ("completed_activities", "completou atividades"),
        ]:
            if e.get(field):
                indicadores.append(f"{label_pt}={e[field]}")
        if indicadores:
            lines.append(f"  Indicadores: {', '.join(indicadores)}")
    return "\n".join(lines)


@router.post("/chat", response_model=DiarySummaryChatResponse)
@inject
async def diary_summary_chat(
    body: DiarySummaryChatRequest,
    current_user: dict = Depends(get_current_user),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
):
    """Chat com a IA para elaborar o Resumo Diário, baseado nas entradas selecionadas."""
    _require_generate(current_user)

    user_id = current_user.get("user_id", "")
    username = current_user.get("full_name") or current_user.get("username", "")

    session_id = body.session_id
    if session_id:
        session = await chat_repo.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")
    else:
        new_session = await chat_repo.create_session(
            user_id=user_id,
            username=username,
            role=current_user.get("role", ""),
            student_id=body.student_id,
            title="Resumo Diário",
        )
        session_id = new_session["id"]

    # Fetch and filter entries server-side: only ones belonging to this student and requested ids
    requested_school_ids = {ref.id for ref in body.entry_ids if ref.type == "school"}
    requested_family_ids = {ref.id for ref in body.entry_ids if ref.type == "family"}

    selected_entries: list[dict] = []
    if requested_school_ids:
        school_entries = await diary_repo.list_by_student(body.student_id, source="school")
        selected_entries.extend([e for e in school_entries if e["id"] in requested_school_ids])
    if requested_family_ids:
        family_entries = await diary_repo.list_by_student(body.student_id, source="family")
        selected_entries.extend([e for e in family_entries if e["id"] in requested_family_ids])

    entries_block = _format_entries_block(selected_entries)
    system_prompt = f"{body.instruction_prompt}\n\n{entries_block}"

    await chat_repo.add_message(
        session_id=session_id,
        role="user",
        content=body.message,
        user_id=user_id,
        username=username,
    )

    try:
        answer, usage = await asyncio.to_thread(
            gemini.generate_text_tracked,
            prompt=body.message,
            system_instruction=system_prompt,
        )
        await usage_repo.log(
            model=usage.model,
            operation="diary_summary_chat",
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            duration_ms=usage.duration_ms,
            user_id=user_id,
            username=username,
        )
    except Exception:
        answer = "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente."

    assistant_msg = await chat_repo.add_message(
        session_id=session_id,
        role="assistant",
        content=answer,
    )

    return DiarySummaryChatResponse(
        session_id=session_id,
        answer=answer,
        message_index=assistant_msg["message_index"],
    )


@router.post("/summaries", status_code=status.HTTP_201_CREATED)
@inject
async def create_summary(
    body: CreateDiarySummaryRequest,
    current_user: dict = Depends(get_current_user),
    summary_repo: DiarySummaryRepository = Depends(Provide[Container.diary_summary_repository]),
):
    """Salva o Resumo Diário gerado para consulta posterior."""
    _require_generate(current_user)

    created = await summary_repo.create(
        student_id=body.student_id,
        author_user_id=current_user.get("user_id", ""),
        period_start=body.period_start,
        period_end=body.period_end,
        summary_text=body.summary_text,
        source_entries=[e.model_dump() for e in body.source_entries],
    )
    return created


@router.get("/summaries")
@inject
async def list_summaries(
    student_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    summary_repo: DiarySummaryRepository = Depends(Provide[Container.diary_summary_repository]),
    parent_repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
):
    """Lista os Resumos Diários salvos de um aluno."""
    _require_view(current_user)

    role = current_user.get("role", "")
    if role == PARENT:
        linked = await parent_repo.is_linked(current_user["user_id"], student_id)
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")

    return await summary_repo.list_by_student(student_id)


@router.delete("/summaries/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user),
    summary_repo: DiarySummaryRepository = Depends(Provide[Container.diary_summary_repository]),
):
    """Remove (soft delete) um Resumo Diário. Apenas o autor ou um admin pode remover."""
    _require_view(current_user)

    existing = await summary_repo.get_by_id(summary_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resumo não encontrado")

    role = current_user.get("role", "")
    if role != ADMIN and existing.get("author_user_id") != current_user.get("user_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    deleted = await summary_repo.delete(summary_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resumo não encontrado")
