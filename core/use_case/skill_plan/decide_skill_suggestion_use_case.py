from core.kernel.result import Result
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository


class DecideSkillSuggestionUseCase:
    """A professora aceita (aplica a nota, com histórico) ou recusa uma sugestão da IA."""

    def __init__(self, repository: ISkillPlanRepository) -> None:
        self.repository = repository

    async def execute(self, suggestion_id: str, accept: bool, user: dict) -> Result:
        decided = await self.repository.decide(suggestion_id, accept, user)
        if not decided:
            return Result.not_found("Sugestão não encontrada ou já decidida.")
        return Result.ok(decided)
