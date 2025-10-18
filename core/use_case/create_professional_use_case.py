from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.professional import Professional
from infrastructure.repositories.professional_repository import ProfessionalRepository

class CreateProfessionalUseCase:
    def __init__(self, professional_repository: ProfessionalRepository):
        self.professional_repository = professional_repository

    async def execute(self, professional: Professional):
        try:
            check_professional = await self.professional_repository.verify(professional)

            if check_professional:
                return Result.bad_request("Profissional já cadastrado")

            professional.created_at = datetime.utcnow()
            professional.updated_at = datetime.utcnow()

            await self.professional_repository.add(professional)

            check_professional = await self.professional_repository.verify(professional)

            if check_professional:
                return Result.ok(check_professional)

            return Result.error(f"Erro ao cadastrar profissional no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar profissional")
