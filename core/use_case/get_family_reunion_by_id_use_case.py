from core.kernel.result import Result
from infrastructure.repositories.family_reunion_repository import FamilyReunionRepository

class GetFamilyReunionByIdUseCase:
    def __init__(self, family_reunion_repository: FamilyReunionRepository):
        self.family_reunion_repository = family_reunion_repository

    async def execute(self, family_reunion_id: int):
        try:
            family_reunion = await self.family_reunion_repository.get_by_id(family_reunion_id)

            if not family_reunion:
                return Result.not_found("Reunião familiar não encontrada")

            return Result.ok(family_reunion)
        except Exception as e:
            return Result.error(f"Erro ao buscar reunião familiar")
