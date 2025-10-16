from core.kernel.result import Result
from infrastructure.repositories.evaluation_repository import EvaluationRepository

class ListEvaluationUseCase:
    def __init__(self, evaluation_repository: EvaluationRepository):
        self.evaluation_repository = evaluation_repository

    async def execute(self):
        try:
            evaluations = await self.evaluation_repository.list_all()
            return Result.ok(evaluations)
        except Exception as e:
            return Result.error(f"Erro ao listar avaliações")
