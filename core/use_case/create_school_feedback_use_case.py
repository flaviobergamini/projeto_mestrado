from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.school_feedback import SchoolFeedback
from infrastructure.repositories.school_feedback_repository import SchoolFeedbackRepository

class CreateSchoolFeedbackUseCase:
    def __init__(self, school_feedback_repository: SchoolFeedbackRepository):
        self.school_feedback_repository = school_feedback_repository

    async def execute(self, school_feedback: SchoolFeedback):
        try:
            check_school_feedback = await self.school_feedback_repository.verify(school_feedback)

            if check_school_feedback:
                return Result.bad_request("Feedback escolar já cadastrado")

            school_feedback.created_at = datetime.utcnow()
            school_feedback.updated_at = datetime.utcnow()

            await self.school_feedback_repository.add(school_feedback)

            check_school_feedback = await self.school_feedback_repository.verify(school_feedback)

            if check_school_feedback:
                return Result.ok(check_school_feedback)

            return Result.error(f"Erro ao cadastrar feedback escolar no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar feedback escolar")
