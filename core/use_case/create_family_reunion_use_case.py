from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.family_reunion import FamilyReunion
from infrastructure.repositories.family_reunion_repository import FamilyReunionRepository

class CreateFamilyReunionUseCase:
    def __init__(self, family_reunion_repository: FamilyReunionRepository):
        self.family_reunion_repository = family_reunion_repository

    async def execute(self, family_reunion: FamilyReunion):
        try:
            check_family_reunion = await self.family_reunion_repository.verify(family_reunion)

            if check_family_reunion:
                return Result.bad_request("Reunião familiar já cadastrada")

            family_reunion.created_at = datetime.utcnow()
            family_reunion.updated_at = datetime.utcnow()

            await self.family_reunion_repository.add(family_reunion)

            check_family_reunion = await self.family_reunion_repository.verify(family_reunion)

            if check_family_reunion:
                return Result.ok(check_family_reunion)

            return Result.error(f"Erro ao cadastrar reunião familiar no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar reunião familiar")
