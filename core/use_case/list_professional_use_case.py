from core.kernel.result import Result
from infrastructure.repositories.professional_repository import ProfessionalRepository

class ListProfessionalUseCase:
    def __init__(self, professional_repository: ProfessionalRepository):
        self.professional_repository = professional_repository

    async def execute(self):
        try:
            professionals = await self.professional_repository.list_all()
            return Result.ok(professionals)
        except Exception as e:
            return Result.error(f"Erro ao listar profissionais")
