from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.professional import Professional
from infrastructure.repositories.professional_repository import ProfessionalRepository

class UpdateProfessionalUseCase:
    def __init__(self, professional_repository: ProfessionalRepository):
        self.professional_repository = professional_repository

    async def execute(self, professional: Professional):
        try:
            check_professional = await self.professional_repository.get_by_id(professional.id)

            if not check_professional:
                return Result.not_found("Profissional não encontrado")

            professional.updated_at = datetime.utcnow()

            updated_professional = await self.professional_repository.update(professional)

            return Result.ok(updated_professional)
        except Exception as e:
            return Result.error(f"Erro ao atualizar profissional")
