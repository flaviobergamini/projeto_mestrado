from core.kernel.result import Result
from infrastructure.repositories.therapeutic_plan_repository import TherapeuticPlanRepository

class GetTherapeuticPlanByIdUseCase:
    def __init__(self, therapeutic_plan_repository: TherapeuticPlanRepository):
        self.therapeutic_plan_repository = therapeutic_plan_repository

    async def execute(self, therapeutic_plan_id: int):
        try:
            therapeutic_plan = await self.therapeutic_plan_repository.get_by_id(therapeutic_plan_id)

            if not therapeutic_plan:
                return Result.not_found("Plano terapêutico não encontrado")

            return Result.ok(therapeutic_plan)
        except Exception as e:
            return Result.error(f"Erro ao buscar plano terapêutico")
