from core.kernel.result import Result
from infrastructure.repositories.family_reunion_repository import FamilyReunionRepository

class ListFamilyReunionUseCase:
    def __init__(self, family_reunion_repository: FamilyReunionRepository):
        self.family_reunion_repository = family_reunion_repository

    async def execute(self):
        try:
            family_reunions = await self.family_reunion_repository.list_all()
            return Result.ok(family_reunions)
        except Exception as e:
            return Result.error(f"Erro ao listar reuniões familiares")
