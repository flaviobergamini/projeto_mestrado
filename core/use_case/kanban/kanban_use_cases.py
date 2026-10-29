"""Use cases do quadro Kanban de execução do PEI."""
from typing import Optional
from core.constants.kanban import KANBAN_STATUSES
from core.kernel.result import Result
from core.interfaces.i_kanban_repository import IKanbanRepository
from core.services.skill_actions import actor_from_user, card_responsible, owns, own_responsible

NOT_FOUND = "Card não encontrado"
# Em cards ligados a uma habilidade, o que veio do plano (ação, descrição e adaptação) não pode ser alterado.
LOCKED_FIELDS_ON_SKILL_CARDS = ("title", "description", "adaptation")


def _invalid_status(status: Optional[str]) -> Optional[str]:
    if status is not None and status not in KANBAN_STATUSES:
        return f"status deve ser um de: {KANBAN_STATUSES}"
    return None


class ListKanbanCardsUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str, user: Optional[dict] = None) -> Result:
        cards = await self.repository.list_by_student(student_id)
        if user is None:
            return Result.ok(cards)
        # cada professor vê só os cards dos quais é responsável; a coordenação (e o admin) vê todos
        actor = actor_from_user(user)
        return Result.ok([c for c in cards if owns(card_responsible(c), actor)])


class CreateKanbanCardUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, data: dict, created_by: str, user: Optional[dict] = None) -> Result:
        error = _invalid_status(data.get("status") or "todo")
        if error:
            return Result.bad_request(error)
        owner = own_responsible(actor_from_user(user)) if user else None  # card manual de professor é dele
        extra = {"responsible_teacher_id": owner["teacher_id"], "responsible_user_id": owner["user_id"],
                 "responsible_name": owner["name"]} if owner else {}
        return Result.ok(await self.repository.create({**data, **extra, "created_by": created_by, "source": "manual"}))


class UpdateKanbanCardUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, card_id: str, data: dict, user: Optional[dict] = None) -> Result:
        error = _invalid_status(data.get("status"))
        if error:
            return Result.bad_request(error)
        reaction = data.get("reaction")
        if reaction is not None and not 1 <= reaction <= 5:
            return Result.bad_request("reaction deve estar entre 1 e 5")
        card = await self.repository.get(card_id)
        if not card or (user is not None and not owns(card_responsible(card), actor_from_user(user))):
            return Result.not_found(NOT_FOUND)  # card de outro professor: para este usuário ele não existe
        if card.get("skill_id"):
            changed = [f for f in LOCKED_FIELDS_ON_SKILL_CARDS if f in data and (data[f] or "") != (card.get(f) or "")]
            if changed:
                return Result.bad_request("Cards ligados a uma habilidade: título, descrição e adaptação vêm do plano e não podem ser alterados aqui.")
            data = {k: v for k, v in data.items() if k not in LOCKED_FIELDS_ON_SKILL_CARDS}
        old_status = card.get("status")
        updated = await self.repository.update(card_id, data)
        if not updated:
            return Result.not_found(NOT_FOUND)
        # As estrelas só mudam quando uma ação entra ou sai de "Concluído"; arrastar entre as outras colunas não mexe nelas.
        if updated.get("skill_id") and "done" in (old_status, updated.get("status")) and old_status != updated.get("status"):
            await self.repository.sync_skill_score(updated["student_id"], updated["skill_id"])
        return Result.ok(updated)


class DeleteKanbanCardUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, card_id: str, user: Optional[dict] = None) -> Result:
        card = await self.repository.get(card_id)
        if not card or (user is not None and not owns(card_responsible(card), actor_from_user(user))) \
                or not await self.repository.delete(card_id):
            return Result.not_found(NOT_FOUND)
        if card.get("skill_id") and card.get("status") == "done":  # só apagar uma ação concluída muda as estrelas
            await self.repository.sync_skill_score(card["student_id"], card["skill_id"])
        return Result.ok(True)


class CreateCardsFromSkillUseCase:
    """Sincroniza os conjuntos do plano da habilidade com o Kanban: cria cards novos e atualiza os já ligados."""

    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str, skill_id: str, created_by: str, only_existing: bool = False) -> Result:
        # criar/atualizar cards a partir do plano NÃO mexe nas estrelas: elas são da professora
        created = await self.repository.create_from_skill(student_id, skill_id, created_by, only_existing)
        return Result.ok(created)


class GenerateKanbanCardSummaryUseCase:
    """A IA resume a execução de uma ação a partir do diário; o resumo fica salvo no card e é o que a
    avaliação posterior da habilidade lê. Habilidade marcada 'sem IA' nunca é enviada ao modelo."""

    def __init__(self, repository: IKanbanRepository, skill_repository, students, ai, prompts) -> None:
        self.repository = repository
        self.skill_repository = skill_repository
        self.students = students
        self.ai = ai
        self.prompts = prompts

    async def execute(self, card_id: str, user: dict) -> Result:
        card = await self.repository.get(card_id)
        if not card or not owns(card_responsible(card), actor_from_user(user)):
            return Result.not_found(NOT_FOUND)
        if not (card.get("daily_log") or "").strip():
            return Result.bad_request("Escreva o diário da ação antes de gerar o resumo.")
        if card.get("skill_id"):
            ctx = await self.skill_repository.skill_context(card["student_id"], card["skill_id"])
            if ctx and ctx["ai_excluded"]:
                return Result.bad_request("Esta habilidade está marcada como 'não trabalhar com a IA'.")
        _, name_map = await self.ai.build_context(card["student_id"], ["student"])
        prompt = (
            f"ID do aluno (anonimizado): {card['student_id']}\n"
            f"Ação: {card['title']}\n"
            f"Adaptação: {card.get('adaptation') or '(vazio)'}\n"
            f"Justificativa: {card.get('description') or '(vazio)'}\n"
            f"Coluna atual no Kanban: {card['status']}\n"
            f"Reação do aluno (1 a 5): {card.get('reaction') or '(não registrada)'}\n"
            f"Diário da ação:\n{card['daily_log']}\n\nEscreva o resumo."
        )
        prompt = self.ai.reanonymize(prompt, name_map)
        text = await self.ai.generate_text(
            "kanban_card_summary", await self.prompts.get("kanban_card_summary"), prompt, user.get("user_id"),
        )
        if not text:
            return Result.err("A IA não devolveu texto. Tente novamente.")
        updated = await self.repository.update(card_id, {"summary": self.ai.deanonymize(text, name_map).strip()})
        return Result.ok(updated)
