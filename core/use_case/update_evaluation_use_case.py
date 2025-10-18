from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.evaluation import Evaluation
from infrastructure.repositories.evaluation_repository import EvaluationRepository

class UpdateEvaluationUseCase:
    def __init__(self, evaluation_repository: EvaluationRepository):
        self.evaluation_repository = evaluation_repository

    async def execute(self, evaluation: Evaluation):
        try:
            check_evaluation = await self.evaluation_repository.get_by_id(evaluation.id)

            if not check_evaluation:
                return Result.not_found("Avaliação não encontrada")

            evaluation.updated_at = datetime.utcnow()

            updated_evaluation = await self.evaluation_repository.update(evaluation)

            return Result.ok(updated_evaluation)
        except Exception as e:
            return Result.error(f"Erro ao atualizar avaliação")
