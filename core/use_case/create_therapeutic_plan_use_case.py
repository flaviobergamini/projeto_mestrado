from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.therapeutic_plan import TherapeuticPlan
from infrastructure.repositories.therapeutic_plan_repository import TherapeuticPlanRepository

class CreateTherapeuticPlanUseCase:
    def __init__(self, therapeutic_plan_repository: TherapeuticPlanRepository):
        self.therapeutic_plan_repository = therapeutic_plan_repository

    async def execute(self, therapeutic_plan: TherapeuticPlan):
        try:
            check_therapeutic_plan = await self.therapeutic_plan_repository.verify(therapeutic_plan)

            if check_therapeutic_plan:
                return Result.bad_request("Plano terapêutico já cadastrado")

            therapeutic_plan.created_at = datetime.utcnow()
            therapeutic_plan.updated_at = datetime.utcnow()

            await self.therapeutic_plan_repository.add(therapeutic_plan)

            check_therapeutic_plan = await self.therapeutic_plan_repository.verify(therapeutic_plan)

            if check_therapeutic_plan:
                return Result.ok(check_therapeutic_plan)

            return Result.error(f"Erro ao cadastrar plano terapêutico no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar plano terapêutico")
