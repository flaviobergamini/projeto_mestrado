from core.kernel.result import Result
from infrastructure.repositories.clinic_repository import ClinicRepository

class DeleteClinicUseCase:
    def __init__(self, clinic_repository: ClinicRepository):
        self.clinic_repository = clinic_repository

    async def execute(self, clinic_id: int):
        try:
            clinic = await self.clinic_repository.get_by_id(clinic_id)

            if not clinic:
                return Result.not_found("Clínica não encontrada")

            await self.clinic_repository.delete(clinic)

            return Result.ok("Clínica deletada com sucesso")
        except Exception as e:
            return Result.error(f"Erro ao deletar clínica")
