from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.autismia import Autismia
from infrastructure.repositories.autismia_repository import AutismiaRepository

class UpdateAutismiaUseCase:
    def __init__(self, autismia_repository: AutismiaRepository):
        self.autismia_repository = autismia_repository

    async def execute(self, autismia: Autismia):
        try:
            check_autismia = await self.autismia_repository.get_by_id(autismia.id)

            if not check_autismia:
                return Result.not_found("Autismia não encontrada")

            autismia.updated_at = datetime.utcnow()

            updated_autismia = await self.autismia_repository.update(autismia)

            return Result.ok(updated_autismia)
        except Exception as e:
            return Result.error(f"Erro ao atualizar autismia")
