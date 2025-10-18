from core.kernel.result import Result
from infrastructure.repositories.autismia_repository import AutismiaRepository

class ListAutismiaUseCase:
    def __init__(self, autismia_repository: AutismiaRepository):
        self.autismia_repository = autismia_repository

    async def execute(self):
        try:
            autismias = await self.autismia_repository.list_all()
            return Result.ok(autismias)
        except Exception as e:
            return Result.error(f"Erro ao listar autismias")
