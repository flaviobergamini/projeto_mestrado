from core.kernel.result import Result
from infrastructure.repositories.therapeutic_plan_repository import TherapeuticPlanRepository

class ListTherapeuticPlanUseCase:
    def __init__(self, therapeutic_plan_repository: TherapeuticPlanRepository):
        self.therapeutic_plan_repository = therapeutic_plan_repository

    async def execute(self):
        try:
            therapeutic_plans = await self.therapeutic_plan_repository.list_all()
            return Result.ok(therapeutic_plans)
        except Exception as e:
            return Result.error(f"Erro ao listar planos terapêuticos")
