"""Resultados de skills salvos por aluno — salvar, listar (sempre filtrado por aluno
no servidor), exportar em PDF e apagar. O download em JSON é montado no cliente a
partir do próprio registro retornado pela listagem."""
import asyncio
import re
import unicodedata
from datetime import date, datetime, timezone
from typing import Optional

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, field_validator

from api.dependencies import require_roles
from core.kernel.container import Container
from infrastructure.repositories.saved_skill_result_repository import SavedSkillResultRepository
from infrastructure.repositories.skill_repository import SkillRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.services.pdf_service import generate_skill_result_pdf

router = APIRouter(prefix="/saved-skills", tags=["Saved Skill Results"])

# Mesmos roles que acessam a página de Chat/Skills
VIEW_ROLES = ("admin", "coordenacao", "professor")


class SavedSkillCreate(BaseModel):
    student_id: str
    skill_id: str
    response: str
    session_id: Optional[str] = None

    @field_validator("response")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("response não pode ser vazio")
        return v


class SkillPdfRequest(BaseModel):
    student_id: str
    skill_title: str
    response: str
    generated_at: Optional[str] = None


def _ascii_slug(text: str, max_len: int = 40) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9_-]+", "_", normalized).strip("_")[:max_len] or "skill"


@router.get("")
@inject
async def list_saved_skill_results(
    student_id: str = Query(..., description="Obrigatório — a listagem é sempre por aluno"),
    skill_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: SavedSkillResultRepository = Depends(Provide[Container.saved_skill_result_repository]),
):
    return await repo.list_by_student(student_id, skill_id=skill_id, date_from=date_from, date_to=date_to)


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def save_skill_result(
    body: SavedSkillCreate,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: SavedSkillResultRepository = Depends(Provide[Container.saved_skill_result_repository]),
    skill_repo: SkillRepository = Depends(Provide[Container.skill_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    skill = await skill_repo.get_by_id(body.skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill não encontrada")
    if not await student_repo.get_by_id(body.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    return await repo.create({
        "student_id": body.student_id,
        "skill_id": skill["id"],
        # o título vem do banco, não do cliente
        "skill_title": skill["title"],
        "response": body.response,
        "session_id": body.session_id,
        "saved_by_user_id": current_user.get("user_id"),
        "saved_by_username": current_user.get("full_name") or current_user.get("username", ""),
    })


@router.post("/pdf")
@inject
async def render_skill_result_pdf(
    body: SkillPdfRequest,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    """Gera o PDF de um resultado de skill sem exigir que ele já esteja salvo —
    serve tanto pro resultado recém-gerado quanto pros itens da lista de salvos."""
    student = await student_repo.get_by_id(body.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    student_name = student.get("name", "")
    generated_at = body.generated_at or datetime.now(timezone.utc).isoformat()

    # ReportLab é síncrono/CPU-bound — thread separada pra não travar o event loop
    pdf_bytes = await asyncio.to_thread(
        generate_skill_result_pdf,
        skill_title=body.skill_title,
        response=body.response,
        student_name=student_name,
        generated_at=generated_at,
    )
    filename = f"{_ascii_slug(body.skill_title)}_{_ascii_slug(student_name, 30)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_saved_skill_result(
    result_id: str,
    current_user: dict = Depends(require_roles(*VIEW_ROLES)),
    repo: SavedSkillResultRepository = Depends(Provide[Container.saved_skill_result_repository]),
):
    item = await repo.get_by_id(result_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resultado não encontrado")
    # admin apaga qualquer um; os demais só os que eles mesmos salvaram
    if current_user.get("role") != "admin" and item["saved_by_user_id"] != current_user.get("user_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você só pode apagar resultados que salvou")
    await repo.delete(result_id)
