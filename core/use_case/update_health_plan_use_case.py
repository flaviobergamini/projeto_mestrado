from core.kernel.result import Result
from infrastructure.models.health_plan import HealthPlan
from infrastructure.models.school import School
from infrastructure.repositories.health_plan_repository import HealthPlanRepository


class UpdateHealthPlanUseCase:
    def __init__(self, health_plan_repository: HealthPlanRepository):
        self.health_plan_repository = health_plan_repository

    async def execute(self, health_plan: HealthPlan):
        try:
            existing_school = await self.health_plan_repository.get_by_id(health_plan.id)
            
            if not existing_school:
                return Result.not_found("Plano de saúde não encontrado")

            updated_school = await self.health_plan_repository.update(health_plan)

            return Result.ok(updated_school)
        except Exception as e:
            return Result.error(f"Erro ao atualizar plano de saúde: {str(e)}")