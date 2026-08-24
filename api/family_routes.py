"""Rotas para pais/responsáveis e terapeutas.

Inclui:
- Gestão de vínculos pai-aluno e terapeuta-aluno (admin)
- Consulta de alunos vinculados (parent/therapist)
- Diário familiar (parent) e diário terapêutico (therapist)
"""

import asyncio
import uuid
import httpx
from datetime import date as _date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, require_roles, require_write
from core.kernel.container import Container
from infrastructure.repositories.parent_student_link_repository import ParentStudentLinkRepository
from infrastructure.repositories.therapist_student_link_repository import TherapistStudentLinkRepository
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.services.rag_service import RagService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.pdf_service import generate_diary_pdf
from infrastructure.services.storage_service import StorageService
from fastapi.responses import Response

router = APIRouter(prefix="/family", tags=["Família e Terapia"])


# ── Modelos ──────────────────────────────────────────────────────────────────


class SetStudentsBody(BaseModel):
    student_ids: list[str]


class FamilyDiaryCreate(BaseModel):
    student_id: str
    diary_date: str
    open_observation: str
    presence: Optional[str] = "Presente"
    absence_reason: Optional[str] = None


class FamilyDiaryUpdate(BaseModel):
    diary_date: Optional[str] = None
    open_observation: Optional[str] = None


class TherapyDiaryCreate(BaseModel):
    student_id: str
    diary_date: str
    open_observation: Optional[str] = None
    presence: Optional[str] = "Presente"
    absence_reason: Optional[str] = None
    # Campos estruturados opcionais para sessão terapêutica
    activity_interest: Optional[str] = None
    participated_in_play: Optional[str] = None
    completed_activities: Optional[str] = None


class TherapyDiaryUpdate(BaseModel):
    diary_date: Optional[str] = None
    presence: Optional[str] = None
    open_observation: Optional[str] = None
    absence_reason: Optional[str] = None
    activity_interest: Optional[str] = None
    participated_in_play: Optional[str] = None
    completed_activities: Optional[str] = None


# ── Vínculos pais ─────────────────────────────────────────────────────────────


@router.get("/parents/{parent_user_id}/students")
@inject
async def get_students_for_parent(
    parent_user_id: str,
    current_user: dict = Depends(get_current_user),
    repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
):
    """Retorna os alunos vinculados a um pai/responsável. Admin vê qualquer; parent vê os seus."""
    role = current_user.get("role", "")
    if role == "parent" and current_user["user_id"] != parent_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return await repo.get_students_for_parent(parent_user_id)


@router.get("/my-students")
@inject
async def get_my_students(
    current_user: dict = Depends(get_current_user),
    parent_repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
    therapist_repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
):
    """Retorna os alunos vinculados ao usuário autenticado (parent ou therapist)."""
    role = current_user.get("role", "")
    user_id = current_user["user_id"]
    if role == "parent":
        return await parent_repo.get_students_for_parent(user_id)
    elif role == "therapist":
        return await therapist_repo.get_students_for_therapist(user_id)
    elif role == "admin":
        return []
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas pais e terapeutas")


@router.put("/parents/{parent_user_id}/students")
@inject
async def set_students_for_parent(
    parent_user_id: str,
    body: SetStudentsBody,
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
):
    """Admin define quais alunos estão vinculados a este pai/responsável."""
    await repo.set_students_for_parent(parent_user_id, body.student_ids)
    return {"ok": True}


@router.get("/students/{student_id}/parents")
@inject
async def get_parents_for_student(
    student_id: str,
    current_user: dict = Depends(require_roles("admin", "coordenacao", "professor")),
    repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
):
    return await repo.get_parents_for_student(student_id)


# ── Vínculos terapeutas ───────────────────────────────────────────────────────


@router.get("/therapists/{therapist_user_id}/students")
@inject
async def get_students_for_therapist(
    therapist_user_id: str,
    current_user: dict = Depends(get_current_user),
    repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
):
    role = current_user.get("role", "")
    if role == "therapist" and current_user["user_id"] != therapist_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return await repo.get_students_for_therapist(therapist_user_id)


@router.put("/therapists/{therapist_user_id}/students")
@inject
async def set_students_for_therapist(
    therapist_user_id: str,
    body: SetStudentsBody,
    current_user: dict = Depends(require_roles("admin", "coordenacao")),
    repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
):
    await repo.set_students_for_therapist(therapist_user_id, body.student_ids)
    return {"ok": True}


@router.get("/students/{student_id}/therapists")
@inject
async def get_therapists_for_student(
    student_id: str,
    current_user: dict = Depends(require_roles("admin", "coordenacao", "professor")),
    repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
):
    return await repo.get_therapists_for_student(student_id)


# ── Diário familiar (pais) ────────────────────────────────────────────────────


async def _fetch_images_map(entry_ids: list[str], diary_repo: DiaryRepository) -> dict[str, list[bytes]]:
    """Download image bytes for a list of diary entry IDs."""
    if not entry_ids:
        return {}
    grouped = await diary_repo.list_images_batch(entry_ids)
    all_keys = [rec["object_key"] for recs in grouped.values() for rec in recs if rec.get("object_key")]
    if not all_keys:
        return {}
    storage = StorageService()
    signed_map = await storage.create_signed_urls_batch_async(all_keys)
    result: dict[str, list[bytes]] = {}
    async with httpx.AsyncClient(timeout=30) as client:
        for entry_id, recs in grouped.items():
            imgs: list[bytes] = []
            for rec in recs:
                url = signed_map.get(rec.get("object_key", "")) or rec.get("public_url", "")
                if url:
                    try:
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            imgs.append(resp.content)
                    except Exception:
                        pass
            if imgs:
                result[entry_id] = imgs
    return result


async def _trigger_embedding(rag: RagService, entry: dict) -> None:
    try:
        await rag.embed_diary_entry(entry)
    except Exception:
        pass


@router.post("/diary/family", status_code=status.HTTP_201_CREATED)
@inject
async def create_family_diary(
    body: FamilyDiaryCreate,
    current_user: dict = Depends(get_current_user),
    parent_repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
):
    """Cria uma entrada de diário familiar. Somente pais vinculados ao aluno."""
    role = current_user.get("role", "")
    if role not in ("admin", "parent"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    if role == "parent":
        linked = await parent_repo.is_linked(current_user["user_id"], body.student_id)
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")

    data = body.model_dump()
    data["source"] = "family"
    data["teacher_name"] = current_user.get("full_name") or current_user.get("username", "")
    entry = await diary_repo.create(data)
    asyncio.create_task(_trigger_embedding(rag, entry))
    return entry


@router.get("/diary/family/{student_id}")
@inject
async def list_family_diary(
    student_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    parent_repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    """Lista entradas de diário familiar de um aluno."""
    role = current_user.get("role", "")
    if role == "parent":
        linked = await parent_repo.is_linked(current_user["user_id"], student_id)
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    elif role not in ("admin", "coordenacao", "professor", "viewer", "therapist", "secretaria"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    return await diary_repo.list_by_student(
        student_id,
        source="family",
        date_from=_date.fromisoformat(date_from) if date_from else None,
        date_to=_date.fromisoformat(date_to) if date_to else None,
    )


# ── Diário de terapia ─────────────────────────────────────────────────────────


@router.post("/diary/therapy", status_code=status.HTTP_201_CREATED)
@inject
async def create_therapy_diary(
    body: TherapyDiaryCreate,
    current_user: dict = Depends(get_current_user),
    therapist_repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
):
    """Cria uma entrada de diário terapêutico. Somente terapeutas vinculados ao aluno."""
    role = current_user.get("role", "")
    if role not in ("admin", "therapist"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    if role == "therapist":
        linked = await therapist_repo.is_linked(current_user["user_id"], body.student_id)
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")

    data = body.model_dump()
    data["source"] = "therapy"
    data["teacher_name"] = current_user.get("full_name") or current_user.get("username", "")
    entry = await diary_repo.create(data)
    asyncio.create_task(_trigger_embedding(rag, entry))
    return entry


@router.get("/diary/therapy/{student_id}")
@inject
async def list_therapy_diary(
    student_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    therapist_repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    """Lista entradas de diário terapêutico de um aluno."""
    role = current_user.get("role", "")
    if role == "therapist":
        linked = await therapist_repo.is_linked(current_user["user_id"], student_id)
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    elif role not in ("admin", "coordenacao", "professor", "viewer", "parent", "secretaria"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    return await diary_repo.list_by_student(
        student_id,
        source="therapy",
        date_from=_date.fromisoformat(date_from) if date_from else None,
        date_to=_date.fromisoformat(date_to) if date_to else None,
    )


@router.get("/export/pdf/family/{student_id}")
@inject
async def export_family_diary_pdf(
    student_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    parent_repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    """Exporta o diário familiar de um aluno em PDF com timbragem."""
    role = current_user.get("role", "")
    if role == "parent":
        linked = await parent_repo.is_linked(current_user["user_id"], student_id)
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    elif role not in ("admin", "coordenacao", "professor", "viewer", "therapist", "secretaria"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    student = await student_repo.get_by_id(student_id)
    entries = await diary_repo.list_by_student(
        student_id,
        source="family",
        date_from=_date.fromisoformat(date_from) if date_from else None,
        date_to=_date.fromisoformat(date_to) if date_to else None,
    )
    entry_ids = [e["id"] for e in entries if e.get("id")]
    images_map = await _fetch_images_map(entry_ids, diary_repo)
    pdf_bytes = generate_diary_pdf(
        entries=entries,
        student_name=(student or {}).get("name", ""),
        diary_label="Diário Familiar",
        date_from=date_from,
        date_to=date_to,
        source="family",
        images_map=images_map,
    )
    safe_name = ((student or {}).get("name") or "aluno").replace(" ", "_")[:40]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Diario_Familiar_{safe_name}.pdf"'},
    )


@router.get("/export/pdf/therapy/{student_id}")
@inject
async def export_therapy_diary_pdf(
    student_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    therapist_repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    """Exporta o diário de terapia de um aluno em PDF com timbragem."""
    role = current_user.get("role", "")
    if role == "therapist":
        linked = await therapist_repo.is_linked(current_user["user_id"], student_id)
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    elif role not in ("admin", "coordenacao", "professor", "viewer", "parent", "secretaria"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    student = await student_repo.get_by_id(student_id)
    entries = await diary_repo.list_by_student(
        student_id,
        source="therapy",
        date_from=_date.fromisoformat(date_from) if date_from else None,
        date_to=_date.fromisoformat(date_to) if date_to else None,
    )
    entry_ids = [e["id"] for e in entries if e.get("id")]
    images_map = await _fetch_images_map(entry_ids, diary_repo)
    pdf_bytes = generate_diary_pdf(
        entries=entries,
        student_name=(student or {}).get("name", ""),
        diary_label="Diário de Terapia",
        date_from=date_from,
        date_to=date_to,
        source="therapy",
        images_map=images_map,
    )
    safe_name = ((student or {}).get("name") or "aluno").replace(" ", "_")[:40]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Diario_Terapia_{safe_name}.pdf"'},
    )


MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/transcribe-audio")
@inject
async def transcribe_family_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
):
    """Transcreve áudio fielmente para uso nos diários familiar e terapêutico."""
    role = current_user.get("role", "")
    if role not in ("admin", "parent", "therapist"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Áudio muito grande. Máximo: 20 MB.")

    content_type = (file.content_type or "").split(";")[0].strip()
    mime_type = content_type if content_type in {
        "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/wav", "audio/x-wav",
    } else "audio/webm"

    try:
        text, usage = await asyncio.to_thread(
            gemini.transcribe_audio_verbatim, content, mime_type=mime_type
        )
        await usage_repo.log(
            model=usage.model,
            operation="family_audio_transcription",
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            duration_ms=usage.duration_ms,
            user_id=current_user.get("user_id"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao transcrever áudio: {str(e)}")

    return {"text": text}


@router.put("/diary/family/{entry_id}")
@inject
async def update_family_diary(
    entry_id: str,
    body: FamilyDiaryUpdate,
    current_user: dict = Depends(get_current_user),
    parent_repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    role = current_user.get("role", "")
    if role not in ("admin", "parent"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    entry = await diary_repo.get_by_id(entry_id)
    if not entry or entry.get("source") != "family":
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if role == "parent":
        linked = await parent_repo.is_linked(current_user["user_id"], entry["student_id"])
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return await diary_repo.update(entry_id, data)


@router.delete("/diary/family/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_family_diary(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    parent_repo: ParentStudentLinkRepository = Depends(Provide[Container.parent_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    role = current_user.get("role", "")
    if role not in ("admin", "parent"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    entry = await diary_repo.get_by_id(entry_id)
    if not entry or entry.get("source") != "family":
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if role == "parent":
        linked = await parent_repo.is_linked(current_user["user_id"], entry["student_id"])
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    await diary_repo.delete(entry_id)


@router.put("/diary/therapy/{entry_id}")
@inject
async def update_therapy_diary(
    entry_id: str,
    body: TherapyDiaryUpdate,
    current_user: dict = Depends(get_current_user),
    therapist_repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    role = current_user.get("role", "")
    if role not in ("admin", "therapist"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    entry = await diary_repo.get_by_id(entry_id)
    if not entry or entry.get("source") != "therapy":
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if role == "therapist":
        linked = await therapist_repo.is_linked(current_user["user_id"], entry["student_id"])
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return await diary_repo.update(entry_id, data)


@router.delete("/diary/therapy/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_therapy_diary(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    therapist_repo: TherapistStudentLinkRepository = Depends(Provide[Container.therapist_student_link_repository]),
    diary_repo: DiaryRepository = Depends(Provide[Container.diary_repository]),
):
    role = current_user.get("role", "")
    if role not in ("admin", "therapist"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    entry = await diary_repo.get_by_id(entry_id)
    if not entry or entry.get("source") != "therapy":
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if role == "therapist":
        linked = await therapist_repo.is_linked(current_user["user_id"], entry["student_id"])
        if not linked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluno não vinculado")
    await diary_repo.delete(entry_id)
