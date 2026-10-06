from core.kernel.result import Result
from core.interfaces.i_skill_plan_repository import ISkillPlanRepository


class ListSkillSuggestionsUseCase:
    def __init__(self, repository: ISkillPlanRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str) -> Result:
        return Result.ok(await self.repository.list_suggestions(student_id))
