from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.therapeutic_plan import TherapeuticPlan
from infrastructure.repositories.therapeutic_plan_repository import TherapeuticPlanRepository

class UpdateTherapeuticPlanUseCase:
    def __init__(self, therapeutic_plan_repository: TherapeuticPlanRepository):
        self.therapeutic_plan_repository = therapeutic_plan_repository

    async def execute(self, therapeutic_plan: TherapeuticPlan):
        try:
            check_therapeutic_plan = await self.therapeutic_plan_repository.get_by_id(therapeutic_plan.id)

            if not check_therapeutic_plan:
                return Result.not_found("Plano terapêutico não encontrado")

            therapeutic_plan.updated_at = datetime.utcnow()

            updated_therapeutic_plan = await self.therapeutic_plan_repository.update(therapeutic_plan)

            return Result.ok(updated_therapeutic_plan)
        except Exception as e:
            return Result.error(f"Erro ao atualizar plano terapêutico")
