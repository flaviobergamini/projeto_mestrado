from datetime import datetime
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.models.health_plan import HealthPlan
from infrastructure.models.school import School
from infrastructure.repositories.health_plan_repository import HealthPlanRepository

class CreateHealthPlanUseCase:
    def __init__(self, health_plan_repository: HealthPlanRepository, jwt_service: JwtService):
        self.health_plan_repository = health_plan_repository
        self.jwt_service = jwt_service

    async def execute(self, heath_plan: HealthPlan):
        try:
            check_heath_plan = await self.health_plan_repository.verify(heath_plan)

            if check_heath_plan:
                return Result.bad_request("Plano de saúde já cadastrado")
            
            heath_plan.created_at = datetime.utcnow()
            heath_plan.updated_at = datetime.utcnow()

            await self.health_plan_repository.add(heath_plan)

            check_heath_plan = await self.health_plan_repository.verify(heath_plan)
            
            if check_heath_plan:
                return Result.ok(check_heath_plan)

            return Result.error(f"Erro ao cadastrar plano de saúde no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar plano de saúde")