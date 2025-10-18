from core.kernel.result import Result
from infrastructure.repositories.professional_repository import ProfessionalRepository

class DeleteProfessionalUseCase:
    def __init__(self, professional_repository: ProfessionalRepository):
        self.professional_repository = professional_repository

    async def execute(self, professional_id: int):
        try:
            professional = await self.professional_repository.get_by_id(professional_id)

            if not professional:
                return Result.not_found("Profissional não encontrado")

            await self.professional_repository.delete(professional)

            return Result.ok("Profissional deletado com sucesso")
        except Exception as e:
            return Result.error(f"Erro ao deletar profissional")
