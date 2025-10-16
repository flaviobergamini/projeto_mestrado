from core.kernel.result import Result
from infrastructure.repositories.evaluation_repository import EvaluationRepository

class GetEvaluationByIdUseCase:
    def __init__(self, evaluation_repository: EvaluationRepository):
        self.evaluation_repository = evaluation_repository

    async def execute(self, evaluation_id: int):
        try:
            evaluation = await self.evaluation_repository.get_by_id(evaluation_id)

            if not evaluation:
                return Result.not_found("Avaliação não encontrada")

            return Result.ok(evaluation)
        except Exception as e:
            return Result.error(f"Erro ao buscar avaliação")
