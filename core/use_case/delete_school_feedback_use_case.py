from core.kernel.result import Result
from infrastructure.repositories.school_feedback_repository import SchoolFeedbackRepository

class DeleteSchoolFeedbackUseCase:
    def __init__(self, school_feedback_repository: SchoolFeedbackRepository):
        self.school_feedback_repository = school_feedback_repository

    async def execute(self, school_feedback_id: int):
        try:
            school_feedback = await self.school_feedback_repository.get_by_id(school_feedback_id)

            if not school_feedback:
                return Result.not_found("Feedback escolar não encontrado")

            await self.school_feedback_repository.delete(school_feedback)

            return Result.ok("Feedback escolar deletado com sucesso")
        except Exception as e:
            return Result.error(f"Erro ao deletar feedback escolar")
