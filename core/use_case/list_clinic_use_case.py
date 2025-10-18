from core.kernel.result import Result
from infrastructure.repositories.clinic_repository import ClinicRepository

class ListClinicUseCase:
    def __init__(self, clinic_repository: ClinicRepository):
        self.clinic_repository = clinic_repository

    async def execute(self):
        try:
            clinics = await self.clinic_repository.list_all()
            return Result.ok(clinics)
        except Exception as e:
            return Result.error(f"Erro ao listar clínicas")
