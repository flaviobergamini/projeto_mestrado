import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from core.constants.functional_profile import DOMAINS, LEVEL_SCALE, DEFAULT_SOURCES
from infrastructure.repositories.functional_profile_repository import FunctionalProfileRepository, ProfileError
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.bncc_context import BnccContext, BNCC_USAGE_RULE
from infrastructure.repositories.bncc_repository import BnccRepository
from infrastructure.services.anonymization_service import AnonymizationService, deanonymize
from infrastructure.utils.functional_profile import normalize_content, parse_model_json, map_strings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/functional-profiles", tags=["Functional Profile"])

READERS = ("admin", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "coordenacao", "professor")


class GenerateBody(BaseModel):
    student_id: str
    sources: Optional[list[str]] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


class ProfileBody(BaseModel):
    student_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    content: Optional[dict[str, Any]] = None


SYSTEM_INSTRUCTION = f"""Você é um especialista em educação especial inclusiva e em Transtorno do Espectro Autista (TEA).
Elabore o PERFIL FUNCIONAL do aluno com base APENAS nas informações do contexto anonimizado fornecido
(resumos do diário, relatórios de habilidades BNCC, estudo de caso, PDI, cadastro, progresso do PEI etc.).

Responda SOMENTE com um objeto JSON válido (sem markdown, sem comentários, sem texto fora do JSON), neste formato:
{{
  "summary": "síntese do funcionamento do aluno em 3 a 5 frases",
  "domains": [
    {{"key": "<chave do domínio>", "level": <1 a 5 ou null>, "description": "até 3 frases",
      "strengths": ["até 4 itens"], "needs": ["até 4 itens"], "supports": ["até 4 estratégias de apoio"],
      "bncc_references": ["até 5 códigos de habilidades do catálogo BNCC ligadas às evidências; [] se o catálogo não foi fornecido"]}}
  ],
  "evidence": ["tipos de registro que sustentam o perfil, ex.: 'resumos do diário', 'relatório BNCC'"]
}}

Domínios (use exatamente estas chaves, um objeto para cada): {", ".join(f"{k} ({v})" for k, v in DOMAINS)}.
Escala de "level": {LEVEL_SCALE}. Use null quando não houver evidência suficiente no contexto — NUNCA invente
dados nem preencha por suposição. Linguagem profissional, objetiva e não estigmatizante, em português do Brasil.
Em "bncc_references" use SOMENTE códigos que existam no catálogo BNCC fornecido; nunca invente códigos.
Quando precisar citar o aluno, use o identificador anonimizado exatamente como fornecido."""


def _build_prompt(student_id: str, school_id: Optional[str], context: str, body: GenerateBody) -> str:
    period = ""
    if body.period_start or body.period_end:
        period = f"\nPeríodo de referência do perfil: {body.period_start or '?'} a {body.period_end or '?'}."
    notes = f"\nOrientações do avaliador: {body.notes.strip()}" if body.notes and body.notes.strip() else ""
    return (
        "DADOS DO ALUNO (ANONIMIZADOS) — copie o identificador EXATAMENTE como fornecido ao citar o aluno ou a escola:\n"
        f"- ID do aluno: {student_id}\n- ID da escola: {school_id or '(não informado)'}{period}{notes}\n\n"
        f"=== CONTEXTO DO ALUNO (ANONIMIZADO) ===\n{context}\n\n"
        "Elabore agora o perfil funcional em JSON."
    )


def _read_only_error(e: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/domains")
async def list_domains(current_user: dict = Depends(require_roles(*READERS))):
    return {"domains": [{"key": k, "label": v} for k, v in DOMAINS], "scale": LEVEL_SCALE}


@router.post("/generate", status_code=status.HTTP_201_CREATED)
@inject
async def generate_profile(
    body: GenerateBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: FunctionalProfileRepository = Depends(Provide[Container.functional_profile_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
    anon_svc: AnonymizationService = Depends(Provide[Container.anonymization_service]),
    bncc_ctx: BnccContext = Depends(Provide[Container.bncc_context]),
    bncc_repo: BnccRepository = Depends(Provide[Container.bncc_repository]),
):
    student = await student_repo.get_by_id(body.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")

    # O perfil funcional nunca usa a si mesmo como fonte.
    sources = [s for s in (body.sources or DEFAULT_SOURCES) if s != "functional_profile"] or DEFAULT_SOURCES
    context, deanon_map = await anon_svc.build_context(body.student_id, sources=sources)
    prompt = _build_prompt(body.student_id, student.get("school_id"), context, body)
    call_kwargs: dict = {"prompt": prompt, "cached_content": None, "cache_fallback_prefix": None}
    if "bncc_catalog" in sources:
        call_kwargs = await bncc_ctx.attach(BNCC_USAGE_RULE + "\n\n" + prompt)
        prompt = call_kwargs["prompt"]

    raw: dict = {}
    last_error = ""
    for attempt in range(2):
        attempt_prompt = prompt if attempt == 0 else prompt + "\n\nATENÇÃO: sua resposta anterior não era um JSON válido. Responda apenas com o objeto JSON."
        try:
            text, usage = await asyncio.to_thread(
                gemini.generate_text_tracked, prompt=attempt_prompt, system_instruction=SYSTEM_INSTRUCTION,
                cached_content=call_kwargs["cached_content"], cache_fallback_prefix=call_kwargs["cache_fallback_prefix"],
            )
            await usage_repo.log(
                model=usage.model, operation="functional_profile_generation",
                input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens, duration_ms=usage.duration_ms, cached_tokens=usage.cached_tokens,
                user_id=current_user.get("user_id"),
            )
            raw = parse_model_json(text)
            break
        except ValueError as e:
            last_error = str(e)
            logger.warning("Perfil funcional: JSON inválido (student_id=%s, tentativa %d): %s", body.student_id, attempt + 1, e)
        except Exception as e:
            logger.exception("Falha ao gerar perfil funcional (student_id=%s)", body.student_id)
            raise HTTPException(status_code=500, detail=f"Erro ao gerar o perfil funcional: {e}")
    else:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"A IA não devolveu um perfil válido ({last_error}). Tente novamente.")

    # Desanonimiza (ID → nome real) cada texto do perfil, como é feito no PEI.
    content = map_strings(normalize_content(raw), lambda s: deanonymize(s, deanon_map))
    # Anti-alucinação: só ficam referências a códigos que realmente existem no catálogo.
    valid_codes = set(await bncc_repo.list_codes())
    for d in content["domains"]:
        d["bncc_references"] = [c for c in d["bncc_references"] if c in valid_codes]
    try:
        return await repo.create(
            body.student_id, content, "ai", current_user, period_start=body.period_start,
            period_end=body.period_end, sources=sources,
        )
    except ProfileError as e:
        raise _read_only_error(e)


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_profile(
    body: ProfileBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: FunctionalProfileRepository = Depends(Provide[Container.functional_profile_repository]),
):
    if not body.student_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o aluno.")
    try:
        return await repo.create(
            body.student_id, body.content or {}, "manual", current_user, title=body.title,
            period_start=body.period_start, period_end=body.period_end,
        )
    except ProfileError as e:
        raise _read_only_error(e)


@router.get("/student/{student_id}")
@inject
async def list_profiles(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: FunctionalProfileRepository = Depends(Provide[Container.functional_profile_repository]),
):
    return await repo.list_for_student(student_id)


@router.get("/student/{student_id}/evolution")
@inject
async def evolution(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: FunctionalProfileRepository = Depends(Provide[Container.functional_profile_repository]),
):
    return await repo.evolution(student_id)


@router.get("/{profile_id}")
@inject
async def get_profile(
    profile_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: FunctionalProfileRepository = Depends(Provide[Container.functional_profile_repository]),
):
    profile = await repo.get(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    return profile


@router.put("/{profile_id}")
@inject
async def update_profile(
    profile_id: str,
    body: ProfileBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: FunctionalProfileRepository = Depends(Provide[Container.functional_profile_repository]),
):
    try:
        updated = await repo.update(
            profile_id, body.content, current_user, title=body.title, period_start=body.period_start,
            period_end=body.period_end, fields_set=body.model_fields_set,
        )
    except ProfileError as e:
        raise _read_only_error(e)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    return updated


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_profile(
    profile_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: FunctionalProfileRepository = Depends(Provide[Container.functional_profile_repository]),
):
    if not await repo.delete(profile_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
