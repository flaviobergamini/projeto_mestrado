from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.autismia import Autismia
from infrastructure.repositories.autismia_repository import AutismiaRepository

class CreateAutismiaUseCase:
    def __init__(self, autismia_repository: AutismiaRepository):
        self.autismia_repository = autismia_repository

    async def execute(self, autismia: Autismia):
        try:
            check_autismia = await self.autismia_repository.verify(autismia)

            if check_autismia:
                return Result.bad_request("Autismia já cadastrada")

            autismia.created_at = datetime.utcnow()
            autismia.updated_at = datetime.utcnow()

            await self.autismia_repository.add(autismia)

            check_autismia = await self.autismia_repository.verify(autismia)

            if check_autismia:
                return Result.ok(check_autismia)

            return Result.error(f"Erro ao cadastrar autismia no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar autismia")
