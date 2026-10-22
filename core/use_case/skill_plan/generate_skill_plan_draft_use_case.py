import logging
from core.constants.bncc_fields import EXPERIENCE_FIELDS
from core.services.skill_actions import normalize_adaptations
from core.kernel.result import Result
from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_prompt_provider import IPromptProvider
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository
from core.interfaces.i_student_reader import IStudentReader
from core.use_case.skill_plan.prompts import ROUND1_SOURCES

logger = logging.getLogger(__name__)


class GenerateSkillPlanDraftUseCase:
    """Rodada 1: propõe adaptações (justificativa + ações) para habilidades do PDI com 1 a 4 estrelas; acrescenta, nunca sobrescreve."""

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
            return Result.bad_request("Nenhuma habilidade elegível: precisa estar no PDI, sem 'não trabalhar com a IA' e com 1 a 4 estrelas.")

        context, name_map = await self.ai.build_context(student_id, ROUND1_SOURCES)
        listing = "\n".join(
            f"- {t['code']} ({t['grade']}, {t['area']}): {t['description']} | nota atual: {t['score']}"
            + (f"\n  Adaptações já existentes (não repetir):\n{t['existing']}" if t["existing"] else "")
            for t in targets
        )
        prompt = (
            f"ID do aluno (anonimizado): {student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
            f"=== HABILIDADES A TRABALHAR ===\n{listing}\n\nGere o JSON."
        )
        prompt = self.ai.reanonymize(prompt, name_map)
        system = await self.prompts.get("skill_plan_round1")
        raw = None
        for attempt in (1, 2):  # o modelo às vezes devolve JSON quebrado (aspas sem escape): uma nova tentativa resolve quase sempre
            try:
                raw = await self.ai.generate_json("skill_plan_round1", system, prompt, user.get("user_id"))
                break
            except ValueError as e:
                logger.warning("Rodada 1: JSON inválido (aluno %s, tentativa %s): %s", student_id, attempt, e)
                if attempt == 2:
                    return Result.err(f"A IA não devolveu JSON válido ({e}). Tente novamente.")

        by_code = {t["code"]: t for t in targets}
        drafts: dict[str, dict] = {}
        for item in raw.get("skills", []):
            target = by_code.get(item.get("code"))  # anti-alucinação: só códigos solicitados
            if not target:
                continue
            raw_groups = item.get("adaptations") or []
            groups = normalize_adaptations(raw_groups if isinstance(raw_groups, list) else [])
            groups = [g for g in groups if g["adaptation"] and g["actions"]]  # toda adaptação tem pelo menos 1 ação
            if not groups:
                continue
            drafts[target["skill_id"]] = {
                "adaptations": [
                    {"adaptation": self.ai.deanonymize(g["adaptation"], name_map),
                     "justification": self.ai.deanonymize(g["justification"], name_map),
                     "actions": [{"action": self.ai.deanonymize(a["action"], name_map)} for a in g["actions"]]}
                    for g in groups
                ],
                "experience_fields": [f for f in (item.get("experience_fields") or []) if f in EXPERIENCE_FIELDS][:5],
            }
        changed = await self.repository.apply_round1(student_id, drafts, user)
        return Result.ok({"requested": len(targets), "filled": len(changed)})
