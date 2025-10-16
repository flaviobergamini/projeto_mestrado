from core.kernel.result import Result
from infrastructure.repositories.school_feedback_repository import SchoolFeedbackRepository

class ListSchoolFeedbackUseCase:
    def __init__(self, school_feedback_repository: SchoolFeedbackRepository):
        self.school_feedback_repository = school_feedback_repository

    async def execute(self):
        try:
            school_feedbacks = await self.school_feedback_repository.list_all()
            return Result.ok(school_feedbacks)
        except Exception as e:
            return Result.error(f"Erro ao listar feedbacks escolares")
