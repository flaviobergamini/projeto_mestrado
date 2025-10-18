from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.school_feedback import SchoolFeedback
from infrastructure.repositories.school_feedback_repository import SchoolFeedbackRepository

class UpdateSchoolFeedbackUseCase:
    def __init__(self, school_feedback_repository: SchoolFeedbackRepository):
        self.school_feedback_repository = school_feedback_repository

    async def execute(self, school_feedback: SchoolFeedback):
        try:
            check_school_feedback = await self.school_feedback_repository.get_by_id(school_feedback.id)

            if not check_school_feedback:
                return Result.not_found("Feedback escolar não encontrado")

            updated_school_feedback = await self.school_feedback_repository.update(
                school_feedback_id=school_feedback.id,
                beneficiary_id=school_feedback.beneficiary_id,
                supervisor_id=school_feedback.supervisor_id,
                feedback_date=school_feedback.feedback_date,
                observation=school_feedback.observation,
                tracking_status=school_feedback.tracking_status,
                updated_at=datetime.utcnow()
            )

            if not updated_school_feedback:
                return Result.not_found("Feedback escolar não encontrado")

            return Result.ok(updated_school_feedback)
        except Exception as e:
            return Result.error(f"Erro ao atualizar feedback escolar: {str(e)}")
