from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.clinic import Clinic
from infrastructure.repositories.clinic_repository import ClinicRepository

class CreateClinicUseCase:
    def __init__(self, clinic_repository: ClinicRepository):
        self.clinic_repository = clinic_repository

    async def execute(self, clinic: Clinic):
        try:
            check_clinic = await self.clinic_repository.verify(clinic)

            if check_clinic:
                return Result.bad_request("Clínica já cadastrada")

            clinic.created_at = datetime.utcnow()
            clinic.updated_at = datetime.utcnow()

            await self.clinic_repository.add(clinic)

            check_clinic = await self.clinic_repository.verify(clinic)

            if check_clinic:
                return Result.ok(check_clinic)

            return Result.error(f"Erro ao cadastrar clínica no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar clínica")
