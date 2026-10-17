import logging
from core.constants.bncc_fields import EXPERIENCE_FIELDS
from core.services.skill_actions import normalize_actions
from core.kernel.result import Result
from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_prompt_provider import IPromptProvider
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository
from core.interfaces.i_student_reader import IStudentReader
from core.use_case.skill_plan.prompts import ROUND1_SOURCES

logger = logging.getLogger(__name__)


class GenerateSkillPlanDraftUseCase:
    """Rodada 1: rascunha adaptação/justificativa/ações das habilidades do PDI (só campos vazios)."""

    def __init__(self, repository: ISkillPlanRepository, students: IStudentReader, ai: IAiGateway, prompts: IPromptProvider) -> None:
        self.prompts = prompts
        self.repository = repository
        self.students = students
        self.ai = ai

    async def execute(self, student_id: str, user: dict) -> Result:
        if not await self.students.get_by_id(student_id):
            return Result.not_found("Aluno não encontrado.")
        targets = await self.repository.plan_skills(student_id)
        if not targets:
            return Result.bad_request("Nenhuma habilidade no PDI disponível para a IA (verifique 'no PDI' e 'sem IA').")

        context, name_map = await self.ai.build_context(student_id, ROUND1_SOURCES)
        listing = "\n".join(
            f"- {t['code']} ({t['grade']}, {t['area']}): {t['description']} | nota atual: {t['score']}" for t in targets
        )
        prompt = (
            f"ID do aluno (anonimizado): {student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
            f"=== HABILIDADES A TRABALHAR ===\n{listing}\n\nGere o JSON."
        )
        try:
            raw = await self.ai.generate_json("skill_plan_round1", await self.prompts.get("skill_plan_round1"), prompt, user.get("user_id"))
        except ValueError as e:
            logger.warning("Rodada 1: JSON inválido (aluno %s): %s", student_id, e)
            return Result.err(f"A IA não devolveu JSON válido ({e}). Tente novamente.")

        by_code = {t["code"]: t for t in targets}
        drafts: dict[str, dict] = {}
        for item in raw.get("skills", []):
            target = by_code.get(item.get("code"))  # anti-alucinação: só códigos solicitados
            if not target:
                continue
            actions = item.get("actions") or []
            drafts[target["skill_id"]] = {
                "adaptation": self.ai.deanonymize(str(item.get("adaptation") or ""), name_map),
                "justification": self.ai.deanonymize(str(item.get("justification") or ""), name_map),
                # cada ação traz a sua adaptação (aceita também texto simples, sem adaptação)
                "actions": [
                    {"action": self.ai.deanonymize(a["action"], name_map), "adaptation": self.ai.deanonymize(a["adaptation"], name_map),
                     "justification": self.ai.deanonymize(a["justification"], name_map)}
                    for a in normalize_actions(actions if isinstance(actions, list) else [str(actions)])
                ],
                "experience_fields": [f for f in (item.get("experience_fields") or []) if f in EXPERIENCE_FIELDS][:5],
            }
        changed = await self.repository.apply_round1(student_id, drafts, user)
        return Result.ok({"requested": len(targets), "filled": len(changed)})
