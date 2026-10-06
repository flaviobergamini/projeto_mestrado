import logging
from core.kernel.result import Result
from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository
from core.interfaces.i_student_reader import IStudentReader
from core.use_case.skill_plan.prompts import ROUND2_SOURCES, ROUND2_SYSTEM

logger = logging.getLogger(__name__)

MAX_STEP = 1  # a IA só pode propor mudança de 1 estrela por vez


class SuggestSkillScoresUseCase:
    """Rodada 2: lê o progresso dos cards do Kanban e SUGERE mudanças de nota (a professora decide)."""

    def __init__(self, repository: ISkillPlanRepository, students: IStudentReader, ai: IAiGateway) -> None:
        self.repository = repository
        self.students = students
        self.ai = ai

    async def execute(self, student_id: str, user: dict) -> Result:
        if not await self.students.get_by_id(student_id):
            return Result.not_found("Aluno não encontrado.")
        targets = await self.repository.plan_skills(student_id)
        cards = await self.repository.cards_by_skill(student_id, [t["skill_id"] for t in targets])
        targets = [t for t in targets if cards.get(t["skill_id"])]
        if not targets:
            return Result.bad_request("Nenhuma habilidade elegível com cards no Kanban para a IA avaliar.")

        context, name_map = await self.ai.build_context(student_id, ROUND2_SOURCES)
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
            f"ID do aluno (anonimizado): {student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
            "=== PROGRESSO NOS CARDS DO KANBAN ===\n"
            + self.ai.reanonymize("\n".join(blocks), name_map) + "\n\nGere o JSON."
        )
        try:
            raw = await self.ai.generate_json("skill_plan_round2", ROUND2_SYSTEM, prompt, user.get("user_id"))
        except ValueError as e:
            logger.warning("Rodada 2: JSON inválido (aluno %s): %s", student_id, e)
            return Result.err(f"A IA não devolveu JSON válido ({e}). Tente novamente.")

        by_code = {t["code"]: t for t in targets}
        items = []
        for it in raw.get("suggestions", []):
            target = by_code.get(it.get("code"))
            try:
                new = int(it.get("suggested_score"))
            except (TypeError, ValueError):
                continue
            # Regras de negócio aplicadas independentemente do que a IA responder.
            if not target or not (0 <= new <= 5) or new == target["score"] or abs(new - target["score"]) > MAX_STEP:
                continue
            valid_ids = {c["id"] for c in cards[target["skill_id"]]}
            items.append({
                "skill_id": target["skill_id"], "current_score": target["score"], "suggested_score": new,
                "reason": self.ai.deanonymize(str(it.get("reason") or ""), name_map),
                "evidence_card_ids": [i for i in (it.get("evidence_card_ids") or []) if i in valid_ids],
            })
        return Result.ok(await self.repository.replace_pending_suggestions(student_id, items))
