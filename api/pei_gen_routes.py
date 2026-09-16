"""PEI generation endpoint — uses anonymised RAG context + Gemini + custom system prompt."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user
from core.kernel.container import Container
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.generated_pei_repository import GeneratedPeiRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.services.rag_service import RagService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.anonymization_service import AnonymizationService, deanonymize
from infrastructure.services.pdf_service import generate_pei_pdf

router = APIRouter(prefix="/pei-gen", tags=["PEI Generation"])


class GeneratePEIRequest(BaseModel):
    student_id: str
    sources: Optional[list[str]] = None
    diary_date_from: Optional[str] = None  # YYYY-MM-DD — diário escolar
    diary_date_to: Optional[str] = None    # YYYY-MM-DD
    family_diary_date_from: Optional[str] = None
    family_diary_date_to: Optional[str] = None
    therapy_diary_date_from: Optional[str] = None
    therapy_diary_date_to: Optional[str] = None


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
    anon_svc: AnonymizationService = Depends(Provide[Container.anonymization_service]),
):
    student = await student_repo.get_by_id(body.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")

    student_name = student.get("name", "")
    generated_by = current_user.get("user_id")

    # Contexto anonimizado (queries estruturadas) e busca RAG (embedding + vetorial)
    # não dependem um do outro — cada um abre sua própria sessão de DB, então
    # rodar em paralelo corta o tempo de espera ao invés de somar os dois.
    (anon_context, deanon_map), rag_context = await asyncio.gather(
        anon_svc.build_context(
            body.student_id,
            diary_limit=15,
            sources=body.sources,
            diary_date_from=body.diary_date_from,
            diary_date_to=body.diary_date_to,
            family_diary_date_from=body.family_diary_date_from,
            family_diary_date_to=body.family_diary_date_to,
            therapy_diary_date_from=body.therapy_diary_date_from,
            therapy_diary_date_to=body.therapy_diary_date_to,
        ),
        rag.build_rag_context(
            query="perfil completo do aluno: comportamento, socialização, habilidades, dificuldades, histórico escolar, família",
            student_id=body.student_id,
            limit=10,
            sources=body.sources,
        ),
    )

    prompt_data = await prompt_repo.get_active("pei")
    system_instruction = prompt_data["content"]

    # Regra de anonimização embutida no código (não no prompt editável pelo admin) —
    # sem essa instrução explícita, o Gemini às vezes vê um UUID solto no JSON e, ao
    # precisar escrever o nome do aluno/escola numa frase, inventa um placeholder tipo
    # "[Nome do Aluno]" em vez de copiar o ID literalmente — aí a desanonimização
    # (deanonymize()) não encontra o UUID na resposta pra substituir pelo nome real.
    # Fica fora de `system_instruction` de propósito: como esse prompt é livremente
    # editável pelo admin, colocar a regra aqui garante que nunca seja removida por engano.
    anonymization_rule = (
        "DADOS DO ALUNO (ANONIMIZADOS) — regra obrigatória: os identificadores abaixo "
        "substituem o nome real do aluno e da escola (limitação técnica do sistema, não "
        "ausência de informação). Sempre que for se referir ao aluno ou à escola pelo nome "
        "no PEI, copie o identificador EXATAMENTE como fornecido abaixo, sem alterá-lo, "
        "sem tentar adivinhar o nome real e sem usar um placeholder genérico como "
        '"[Nome do Aluno]" ou "[Nome da Escola]":\n'
        f"- ID do aluno: {body.student_id}\n"
        f"- ID da escola: {student.get('school_id') or '(não informado)'}"
    )

    prompt = f"""Com base nos dados anonimizados abaixo, gere o PEI completo.

{anonymization_rule}

=== CONTEXTO DO ALUNO (ANONIMIZADO) ===
{anon_context}

=== REGISTROS SIMILARES (RAG) ===
{rag_context}

Gere o Plano Educacional Individualizado (PEI) completo para este aluno."""

    try:
        # Chamada síncrona e bloqueante — roda em thread separada para não
        # travar o event loop (e todas as outras requisições) durante a
        # geração ou um retry por rate limit do Gemini.
        raw_pei, usage = await asyncio.to_thread(
            gemini.generate_text_tracked,
            prompt=prompt,
            system_instruction=system_instruction,
        )
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

    # De-anonymise: replace UUIDs with real names in the generated PEI
    pei_text = deanonymize(raw_pei, deanon_map)

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
        "debug_prompt": prompt,
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


@router.get("/pdf/{pei_id}")
@inject
async def download_pei_pdf(
    pei_id: str,
    current_user: dict = Depends(get_current_user),
    pei_repo: GeneratedPeiRepository = Depends(Provide[Container.generated_pei_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    """Generate and return a PDF for the given saved PEI."""
    pei = await pei_repo.get_by_id(pei_id)
    if not pei:
        raise HTTPException(status_code=404, detail="PEI não encontrado.")

    student_name = pei.get("student_name") or ""
    if not student_name:
        student = await student_repo.get_by_id(pei["student_id"])
        student_name = (student or {}).get("name", "") if student else ""

    # síncrona/CPU-bound (ReportLab) — roda em thread separada pra não travar o event loop
    pdf_bytes = await asyncio.to_thread(
        generate_pei_pdf,
        pei_text=pei["pei_text"],
        student_name=student_name,
        generated_at=str(pei.get("generated_at", "")),
    )

    safe_name = student_name.replace(" ", "_")[:40]
    filename = f"PEI_{safe_name}_{pei_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
