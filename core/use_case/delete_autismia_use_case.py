from core.kernel.result import Result
from infrastructure.repositories.autismia_repository import AutismiaRepository

class DeleteAutismiaUseCase:
    def __init__(self, autismia_repository: AutismiaRepository):
        self.autismia_repository = autismia_repository

    async def execute(self, autismia_id: int):
        try:
            autismia = await self.autismia_repository.get_by_id(autismia_id)

            if not autismia:
                return Result.not_found("Autismia não encontrada")

            await self.autismia_repository.delete(autismia)

            return Result.ok("Autismia deletada com sucesso")
        except Exception as e:
            return Result.error(f"Erro ao deletar autismia")
