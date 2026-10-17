from core.kernel.result import Result
from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_prompt_provider import IPromptProvider
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository
from core.interfaces.i_student_reader import IStudentReader
from core.use_case.skill_plan.prompts import STAR_SCALE


class GenerateSkillSummaryUseCase:
    """Gera (sem salvar) o resumo de uma habilidade; a professora revisa/edita e salva junto com o plano.

    Respeita "não trabalhar com a IA": habilidade marcada assim nunca é enviada ao modelo."""

    def __init__(self, repository: ISkillPlanRepository, students: IStudentReader, ai: IAiGateway,
                 prompts: IPromptProvider) -> None:
        self.repository = repository
        self.students = students
        self.ai = ai
        self.prompts = prompts

    async def execute(self, student_id: str, skill_id: str, user: dict) -> Result:
        if not await self.students.get_by_id(student_id):
            return Result.not_found("Aluno não encontrado.")
        ctx = await self.repository.skill_context(student_id, skill_id)
        if not ctx:
            return Result.not_found("Habilidade não encontrada.")
        if ctx["ai_excluded"]:
            return Result.bad_request("Esta habilidade está marcada como 'não trabalhar com a IA'.")

        _, name_map = await self.ai.build_context(student_id, ["student"])
        cards = "\n".join(
            f"  * {c['status']} | {c['title']}" + (f" | registro: {c['daily_log']}" if c["daily_log"] else "")
            for c in ctx["cards"]
        ) or "  (nenhum card)"
        history = "\n".join(
            f"  * {h['at']}: nota {h['old']} -> {h['new']}" + (f" ({h['note']})" if h["note"] else "")
            for h in ctx["score_history"]
        ) or "  (sem mudanças registradas)"
        prompt = (
            f"ID do aluno (anonimizado): {student_id}\n"
            f"Escala da nota: {STAR_SCALE}\n\n"
            f"Habilidade {ctx['code']} ({ctx['grade']}, {ctx['area']}): {ctx['description']}\n"
            f"Nota atual: {ctx['score']}\n"
            f"Adaptação: {ctx['adaptation'] or '(vazio)'}\n"
            f"Justificativa: {ctx['justification'] or '(vazio)'}\n"
            f"Ações práticas: {ctx['actions'] or '(vazio)'}\n"
            f"Observação do professor: {ctx['observation'] or '(vazio)'}\n"
            f"Histórico de notas:\n{history}\n"
            f"Progresso nos cards do Kanban:\n{cards}\n\n"
            "Escreva o resumo."
        )
        prompt = self.ai.reanonymize(prompt, name_map)
        text = await self.ai.generate_text(
            "skill_summary", await self.prompts.get("skill_summary"), prompt, user.get("user_id"),
        )
        if not text:
            return Result.err("A IA não devolveu texto. Tente novamente.")
        return Result.ok({"summary": self.ai.deanonymize(text, name_map)})
