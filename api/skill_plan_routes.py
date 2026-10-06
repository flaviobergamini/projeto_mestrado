"""Plano por habilidade com IA: rodada 1 (rascunho do quadro) e rodada 2 (sugestão de mudança de nota).

A IA só trabalha habilidades marcadas 'no PDI' e NÃO marcadas como 'sem IA'. Ela nunca altera notas
sozinha: a rodada 2 apenas propõe; a professora aceita ou recusa."""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from infrastructure.repositories.skill_plan_repository import SkillPlanRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.anonymization_service import AnonymizationService, deanonymize, reanonymize
from infrastructure.utils.functional_profile import parse_model_json, map_strings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skill-plan", tags=["Skill Plan"])

READERS = ("admin", "secretaria", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "coordenacao", "professor")

ROUND1_SOURCES = ["student", "school", "case_study", "functional_profile", "diary_summary", "skill_report"]
ROUND2_SOURCES = ["student", "functional_profile", "diary_summary"]

STAR_SCALE = (
    "0 = não avaliada; 1 = dependência total (ajuda física total); 2 = ajuda física parcial; "
    "3 = ajuda gestual ou verbal; 4 = pista mínima/supervisão; 5 = independente"
)

ROUND1_SYSTEM = f"""Você é especialista em educação inclusiva e em TEA. Para CADA habilidade BNCC listada, redija o quadro
da habilidade com base APENAS no contexto anonimizado fornecido. Escala de apoio da nota atual: {STAR_SCALE}.
Responda SOMENTE com JSON válido, sem markdown:
{{"skills": [{{"code": "<código exato>", "adaptation": "como adaptar a atividade/ambiente (2 a 4 frases)",
  "justification": "por que esta adaptação, ligando às evidências do contexto (2 a 4 frases)",
  "actions": ["3 a 5 ações práticas, curtas e observáveis"],
  "correlated_codes": ["até 3 códigos de habilidades pré-requisito ou relacionadas; [] se não houver certeza"]}}]}}
Não invente fatos nem diagnósticos que não estejam no contexto; se faltar evidência, diga isso na justificativa.
Use SOMENTE os códigos fornecidos na lista. Use o identificador anonimizado do aluno exatamente como fornecido."""

ROUND2_SYSTEM = f"""Você é especialista em educação inclusiva e em TEA. Avalie, para cada habilidade BNCC, se o progresso registrado
nos cards do Kanban (títulos, status, registros do dia, reação) justifica alterar a nota atual. Escala: {STAR_SCALE}.
Regras: sugira mudança de NO MÁXIMO 1 estrela por vez; só sugira quando houver evidência concreta nos cards; se não
houver evidência suficiente, NÃO inclua a habilidade. Você apenas propõe — a professora decide.
Responda SOMENTE com JSON válido, sem markdown:
{{"suggestions": [{{"code": "<código exato>", "suggested_score": <0 a 5>, "reason": "justificativa objetiva citando os registros",
  "evidence_card_ids": ["ids dos cards usados, exatamente como fornecidos"]}}]}}"""


class StudentBody(BaseModel):
    student_id: str


class DecideBody(BaseModel):
    accept: bool


async def _call(gemini, usage_repo, user, operation, system, prompt):
    text, usage = await asyncio.to_thread(
        gemini.generate_text_tracked, prompt=prompt, system_instruction=system,
        cached_content=None, cache_fallback_prefix=None,
    )
    await usage_repo.log(
        model=usage.model, operation=operation, input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens, duration_ms=usage.duration_ms, cached_tokens=usage.cached_tokens,
        user_id=user.get("user_id"),
    )
    return parse_model_json(text)


@router.post("/round1")
@inject
async def round1(
    body: StudentBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: SkillPlanRepository = Depends(Provide[Container.skill_plan_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
    anon_svc: AnonymizationService = Depends(Provide[Container.anonymization_service]),
):
    """Rodada 1: rascunha adaptação/justificativa/ações das habilidades do PDI (só campos vazios)."""
    if not await student_repo.get_by_id(body.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    targets = await repo.plan_skills(body.student_id)
    if not targets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Nenhuma habilidade no PDI disponível para a IA (verifique 'no PDI' e 'sem IA').")
    context, deanon_map = await anon_svc.build_context(body.student_id, sources=ROUND1_SOURCES)
    listing = "\n".join(
        f"- {t['code']} ({t['grade']}, {t['area']}): {t['description']} | nota atual: {t['score']}" for t in targets
    )
    prompt = (
        f"ID do aluno (anonimizado): {body.student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
        f"=== HABILIDADES A TRABALHAR ===\n{listing}\n\nGere o JSON."
    )
    try:
        raw = await _call(gemini, usage_repo, current_user, "skill_plan_round1", ROUND1_SYSTEM, prompt)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"A IA não devolveu JSON válido ({e}). Tente novamente.")
    except Exception as e:
        logger.exception("Falha na rodada 1 do plano de habilidades")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o plano: {e}")

    by_code = {t["code"]: t for t in targets}
    drafts: dict[str, dict] = {}
    for item in raw.get("skills", []):
        t = by_code.get(item.get("code"))  # anti-alucinação: só códigos solicitados
        if not t:
            continue
        item = map_strings(item, lambda s: deanonymize(s, deanon_map))
        actions = item.get("actions") or []
        drafts[t["skill_id"]] = {
            "adaptation": item.get("adaptation") or "",
            "justification": item.get("justification") or "",
            "actions": "\n".join(str(a).strip() for a in actions) if isinstance(actions, list) else str(actions),
            "correlated_codes": [c for c in (item.get("correlated_codes") or []) if isinstance(c, str)][:3],
        }
    changed = await repo.apply_round1(body.student_id, drafts, current_user)
    return {"requested": len(targets), "filled": len(changed)}


@router.post("/round2")
@inject
async def round2(
    body: StudentBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: SkillPlanRepository = Depends(Provide[Container.skill_plan_repository]),
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
    anon_svc: AnonymizationService = Depends(Provide[Container.anonymization_service]),
):
    """Rodada 2: lê o progresso dos cards e SUGERE mudanças de nota (a professora aceita/recusa)."""
    if not await student_repo.get_by_id(body.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")
    targets = await repo.plan_skills(body.student_id)
    cards = await repo.cards_by_skill(body.student_id, [t["skill_id"] for t in targets])
    targets = [t for t in targets if cards.get(t["skill_id"])]
    if not targets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Nenhuma habilidade elegível com cards no Kanban para a IA avaliar.")
    context, deanon_map = await anon_svc.build_context(body.student_id, sources=ROUND2_SOURCES)
    blocks = []
    for t in targets:
        lines = [
            f"  * id={c['id']} | {c['status']} | {c['title']}"
            + (f" | registro: {c['daily_log']}" if c["daily_log"] else "")
            + (f" | reação: {c['reaction']}/5" if c["reaction"] else "")
            for c in cards[t["skill_id"]]
        ]
        blocks.append(f"- {t['code']}: {t['description']} | nota atual: {t['score']}\n" + "\n".join(lines))
    prompt = (
        f"ID do aluno (anonimizado): {body.student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
        "=== PROGRESSO NOS CARDS DO KANBAN ===\n" + reanonymize("\n".join(blocks), deanon_map) + "\n\nGere o JSON."
    )
    try:
        raw = await _call(gemini, usage_repo, current_user, "skill_plan_round2", ROUND2_SYSTEM, prompt)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"A IA não devolveu JSON válido ({e}). Tente novamente.")
    except Exception as e:
        logger.exception("Falha na rodada 2 do plano de habilidades")
        raise HTTPException(status_code=500, detail=f"Erro ao avaliar o progresso: {e}")

    by_code = {t["code"]: t for t in targets}
    items = []
    for it in raw.get("suggestions", []):
        t = by_code.get(it.get("code"))
        try:
            new = int(it.get("suggested_score"))
        except (TypeError, ValueError):
            continue
        # Regras de segurança aplicadas no servidor, independentemente da IA.
        if not t or not (0 <= new <= 5) or new == t["score"] or abs(new - t["score"]) > 1:
            continue
        valid_ids = {c["id"] for c in cards[t["skill_id"]]}
        items.append({
            "skill_id": t["skill_id"], "current_score": t["score"], "suggested_score": new,
            "reason": deanonymize(str(it.get("reason") or ""), deanon_map),
            "evidence_card_ids": [i for i in (it.get("evidence_card_ids") or []) if i in valid_ids],
        })
    return await repo.replace_pending_suggestions(body.student_id, items)


@router.get("/suggestions")
@inject
async def list_suggestions(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    repo: SkillPlanRepository = Depends(Provide[Container.skill_plan_repository]),
):
    return await repo.list_suggestions(student_id)


@router.post("/suggestions/{suggestion_id}/decide")
@inject
async def decide_suggestion(
    suggestion_id: str,
    body: DecideBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    repo: SkillPlanRepository = Depends(Provide[Container.skill_plan_repository]),
):
    result = await repo.decide(suggestion_id, body.accept, current_user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sugestão não encontrada ou já decidida.")
    return result
