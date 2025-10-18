from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.family_reunion import FamilyReunion
from infrastructure.repositories.family_reunion_repository import FamilyReunionRepository

class UpdateFamilyReunionUseCase:
    def __init__(self, family_reunion_repository: FamilyReunionRepository):
        self.family_reunion_repository = family_reunion_repository

    async def execute(self, family_reunion: FamilyReunion):
        try:
            check_family_reunion = await self.family_reunion_repository.get_by_id(family_reunion.id)

            if not check_family_reunion:
                return Result.not_found("Reunião familiar não encontrada")

            family_reunion.updated_at = datetime.utcnow()

            updated_family_reunion = await self.family_reunion_repository.update(family_reunion)

            return Result.ok(updated_family_reunion)
        except Exception as e:
            return Result.error(f"Erro ao atualizar reunião familiar")
