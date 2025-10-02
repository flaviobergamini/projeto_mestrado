from core.kernel.result import Result
from infrastructure.repositories.health_plan_repository import HealthPlanRepository


class GetHealthPlanByIdUseCase:
    def __init__(self, health_plan_repository: HealthPlanRepository):
        self.health_plan_repository = health_plan_repository

    async def execute(self, school_id: int):
        try:
            health_plan = await self.health_plan_repository.get_by_id(school_id)
            if not health_plan:
                return Result.not_found("Plano de Saúde não encontrado")
            return Result.ok(health_plan)
        except Exception as e:
            return Result.error(f"Erro ao obter plano de saúde por ID")