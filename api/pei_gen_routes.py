"""PEI generation endpoint — uses RAG context + Gemini + custom system prompt."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user
from core.kernel.container import Container
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.generated_pei_repository import GeneratedPeiRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.rag_service import RagService
from infrastructure.services.gemini_service import GeminiService

router = APIRouter(prefix="/pei-gen", tags=["PEI Generation"])


class GeneratePEIRequest(BaseModel):
    student_id: str
    sources: Optional[list[str]] = None  # e.g. ["diary", "case_study"]


@router.post("/generate")
@inject
async def generate_pei(
    body: GeneratePEIRequest,
    current_user: dict = Depends(get_current_user),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    prompt_repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
    pei_repo: GeneratedPeiRepository = Depends(Provide[Container.generated_pei_repository]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
):
    student = await student_repo.get_by_id(body.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")

    student_name = student.get("name", "")

    rag_context = await rag.build_rag_context(
        query="perfil completo do aluno: comportamento, socialização, habilidades, dificuldades, histórico escolar, família",
        student_id=body.student_id,
        student_name=student_name,
        limit=10,
        sources=body.sources,
    )

    prompt_data = await prompt_repo.get_active("pei")
    system_instruction = prompt_data["content"]

    prompt = f"""Com base nas seguintes informações sobre o aluno {student_name}, gere o PEI completo:

{rag_context}

Gere o Plano Educacional Individualizado (PEI) completo para este aluno."""

    try:
        pei_text, usage = gemini.generate_text_tracked(prompt=prompt, system_instruction=system_instruction)
        await usage_repo.log(
            model=usage.model,
            operation="pei_generation",
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            duration_ms=usage.duration_ms,
            user_id=generated_by,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PEI: {str(e)}")

    # Persist generated PEI
    generated_by = current_user.get("user_id")
    saved = await pei_repo.save(
        student_id=body.student_id,
        student_name=student_name,
        pei_text=pei_text,
        sources_used=body.sources,
        generated_by=generated_by,
    )

    return {
        "id": saved["id"],
        "student_id": body.student_id,
        "student_name": student_name,
        "pei_text": pei_text,
        "generated_at": saved["generated_at"],
    }


@router.get("/saved")
@inject
async def list_saved_peis(
    student_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    pei_repo: GeneratedPeiRepository = Depends(Provide[Container.generated_pei_repository]),
):
    """List previously generated PEIs for a student."""
    return await pei_repo.list_by_student(student_id)


@router.get("/saved/{pei_id}")
@inject
async def get_saved_pei(
    pei_id: str,
    current_user: dict = Depends(get_current_user),
    pei_repo: GeneratedPeiRepository = Depends(Provide[Container.generated_pei_repository]),
):
    pei = await pei_repo.get_by_id(pei_id)
    if not pei:
        raise HTTPException(status_code=404, detail="PEI não encontrado.")
    return pei


@router.delete("/saved/{pei_id}", status_code=204)
@inject
async def delete_saved_pei(
    pei_id: str,
    current_user: dict = Depends(get_current_user),
    pei_repo: GeneratedPeiRepository = Depends(Provide[Container.generated_pei_repository]),
):
    deleted = await pei_repo.delete(pei_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="PEI não encontrado.")
