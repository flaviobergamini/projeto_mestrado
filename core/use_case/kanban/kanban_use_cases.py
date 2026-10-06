"""Use cases do quadro Kanban de execução do PEI."""
from typing import Optional
from core.constants.kanban import KANBAN_STATUSES
from core.kernel.result import Result
from core.interfaces.i_kanban_repository import IKanbanRepository

NOT_FOUND = "Card não encontrado"


def _invalid_status(status: Optional[str]) -> Optional[str]:
    if status is not None and status not in KANBAN_STATUSES:
        return f"status deve ser um de: {KANBAN_STATUSES}"
    return None


class ListKanbanCardsUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str) -> Result:
        return Result.ok(await self.repository.list_by_student(student_id))


class CreateKanbanCardUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, data: dict, created_by: str) -> Result:
        error = _invalid_status(data.get("status") or "todo")
        if error:
            return Result.bad_request(error)
        return Result.ok(await self.repository.create({**data, "created_by": created_by, "source": "manual"}))


class UpdateKanbanCardUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, card_id: str, data: dict) -> Result:
        error = _invalid_status(data.get("status"))
        if error:
            return Result.bad_request(error)
        reaction = data.get("reaction")
        if reaction is not None and not 1 <= reaction <= 5:
            return Result.bad_request("reaction deve estar entre 1 e 5")
        updated = await self.repository.update(card_id, data)
        return Result.ok(updated) if updated else Result.not_found(NOT_FOUND)


class DeleteKanbanCardUseCase:
    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, card_id: str) -> Result:
        return Result.ok(True) if await self.repository.delete(card_id) else Result.not_found(NOT_FOUND)


class CreateCardsFromSkillUseCase:
    """Envia as ações práticas do plano de uma habilidade para o Kanban (sem duplicar)."""

    def __init__(self, repository: IKanbanRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str, skill_id: str, created_by: str) -> Result:
        return Result.ok(await self.repository.create_from_skill(student_id, skill_id, created_by))
