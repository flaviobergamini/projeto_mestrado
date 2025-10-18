from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.evaluation import Evaluation
from infrastructure.repositories.evaluation_repository import EvaluationRepository

class CreateEvaluationUseCase:
    def __init__(self, evaluation_repository: EvaluationRepository):
        self.evaluation_repository = evaluation_repository

    async def execute(self, evaluation: Evaluation):
        try:
            check_evaluation = await self.evaluation_repository.verify(evaluation)

            if check_evaluation:
                return Result.bad_request("Avaliação já cadastrada")

            evaluation.created_at = datetime.utcnow()
            evaluation.updated_at = datetime.utcnow()

            await self.evaluation_repository.add(evaluation)

            check_evaluation = await self.evaluation_repository.verify(evaluation)

            if check_evaluation:
                return Result.ok(check_evaluation)

            return Result.error(f"Erro ao cadastrar avaliação no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar avaliação")
