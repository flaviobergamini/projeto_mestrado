from core.kernel.result import Result
from infrastructure.repositories.health_plan_repository import HealthPlanRepository


class ListHealthPlanUseCase:
    def __init__(self, health_plan_repository: HealthPlanRepository):
        self.health_plan_repository = health_plan_repository
    
    async def execute(self):
        try:
            health_plans = await self.health_plan_repository.list_all()
            return Result.ok(health_plans)
        except Exception as e:
            return Result.error(f"Erro ao listar planos de saúde")