from core.kernel.result import Result
from infrastructure.models.school import School
from infrastructure.repositories.health_plan_repository import HealthPlanRepository


class DeleteHealthPlanUseCase:
    def __init__(self, health_plan_repository: HealthPlanRepository):
        self.health_plan_repository = health_plan_repository

    async def execute(self, health_plan_id: int):
        try:
            existing_health_plan = await self.health_plan_repository.get_by_id(health_plan_id)
            
            if not existing_health_plan:
                return Result.not_found("Plano de saúde não encontrada")

            await self.health_plan_repository.delete(existing_health_plan)

            return Result.ok(existing_health_plan)
        except Exception as e:
            return Result.error(f"Erro ao deletar plano de saúde: {str(e)}")