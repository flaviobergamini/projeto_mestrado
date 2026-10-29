import logging
from core.constants.bncc_fields import EXPERIENCE_FIELDS
from core.services.skill_actions import normalize_adaptations
from core.kernel.result import Result
from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_prompt_provider import IPromptProvider
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository
from core.interfaces.i_student_reader import IStudentReader
from core.use_case.skill_plan.prompts import (
    ROUND1_SOURCES, SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_LIMITS,
)

logger = logging.getLogger(__name__)


class GenerateSkillPlanDraftUseCase:
    """Rodada 1: propõe adaptações (justificativa + ações) para habilidades com 1 a 4 estrelas; acrescenta, nunca sobrescreve.
    Não altera estrelas: a nota é decisão da professora."""

    def __init__(self, repository: ISkillPlanRepository, students: IStudentReader, ai: IAiGateway, prompts: IPromptProvider,
                 settings) -> None:
        self.settings = settings
        self.prompts = prompts
        self.repository = repository
        self.students = students
        self.ai = ai

    async def build_request(self, student_id: str) -> Result:
        """Monta o que é enviado à IA (sem chamá-la): prompt do sistema, texto do pedido e limites. Usado também na prévia."""
        if not await self.students.get_by_id(student_id):
            return Result.not_found("Aluno não encontrado.")
        targets = await self.repository.plan_skills(student_id)
        if not targets:
            return Result.bad_request("Nenhuma habilidade elegível: precisa ter 'Trabalhar com a IA' marcado e de 1 a 4 estrelas.")

        limits = await self.settings.get(SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_LIMITS)
        context, name_map = await self.ai.build_context(student_id, ROUND1_SOURCES)
        listing = "\n".join(
            f"- {t['code']} ({t['grade']}, {t['area']}): {t['description']} | nota atual: {t['score']} de 5 estrelas "
            f"(faltam {5 - t['score']} para a habilidade ficar consolidada)"
            + (f"\n  Adaptações já existentes (não repetir):\n{t['existing']}" if t["existing"] else "")
            for t in targets
        )
        prompt = (
            f"ID do aluno (anonimizado): {student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
            f"=== HABILIDADES A TRABALHAR ===\n{listing}\n\n"
            f"=== LIMITES DESTA GERAÇÃO ===\nNo máximo {limits['max_adaptations']} adaptação(ões) por habilidade e no máximo "
            f"{limits['max_actions']} ação(ões) por adaptação. Use menos quando a necessidade do aluno for menor.\n\nGere o JSON."
        )
        prompt = self.ai.reanonymize(prompt, name_map)
        system = await self.prompts.get("skill_plan_round1")
        return Result.ok({"targets": targets, "limits": limits, "name_map": name_map, "system": system, "prompt": prompt})

    async def preview(self, student_id: str) -> Result:
        """O que seria enviado à IA para este aluno (já anonimizado), sem chamar a IA e sem custo."""
        built = await self.build_request(student_id)
        if not built.is_ok:
            return built
        v = built.value
        return Result.ok({"system": v["system"], "prompt": v["prompt"], "limits": v["limits"],
                          "sources": ROUND1_SOURCES, "skills": len(v["targets"])})

    async def execute(self, student_id: str, user: dict) -> Result:
        built = await self.build_request(student_id)
        if not built.is_ok:
            return built
        targets, limits, name_map = built.value["targets"], built.value["limits"], built.value["name_map"]
        system, prompt = built.value["system"], built.value["prompt"]
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
            # respeita os limites máximos configurados pelo administrador
            groups = [{**g, "actions": g["actions"][:limits["max_actions"]]} for g in groups[:limits["max_adaptations"]]]
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
