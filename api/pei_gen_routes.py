"""PEI generation endpoint — uses RAG context + Gemini + custom system prompt."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user
from core.kernel.container import Container
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.services.rag_service import RagService
from infrastructure.services.gemini_service import GeminiService

router = APIRouter(prefix="/pei-gen", tags=["PEI Generation"])


class GeneratePEIRequest(BaseModel):
    student_id: str


@router.post("/generate")
@inject
async def generate_pei(
    body: GeneratePEIRequest,
    current_user: dict = Depends(get_current_user),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    rag: RagService = Depends(Provide[Container.rag_service]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    prompt_repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
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
    )

    prompt_data = await prompt_repo.get_active("pei")
    system_instruction = prompt_data["content"]

    prompt = f"""Com base nas seguintes informações sobre o aluno {student_name}, gere o PEI completo:

{rag_context}

Gere o Plano Educacional Individualizado (PEI) completo para este aluno."""

    try:
        pei_text = gemini.generate_text(prompt=prompt, system_instruction=system_instruction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PEI: {str(e)}")

    return {
        "student_id": body.student_id,
        "student_name": student_name,
        "pei_text": pei_text,
    }
