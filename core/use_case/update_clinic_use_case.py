from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.clinic import Clinic
from infrastructure.repositories.clinic_repository import ClinicRepository

class UpdateClinicUseCase:
    def __init__(self, clinic_repository: ClinicRepository):
        self.clinic_repository = clinic_repository

    async def execute(self, clinic: Clinic):
        try:
            check_clinic = await self.clinic_repository.get_by_id(clinic.id)

            if not check_clinic:
                return Result.not_found("Clínica não encontrada")

            clinic.updated_at = datetime.utcnow()

            updated_clinic = await self.clinic_repository.update(clinic)

            return Result.ok(updated_clinic)
        except Exception as e:
            return Result.error(f"Erro ao atualizar clínica")
