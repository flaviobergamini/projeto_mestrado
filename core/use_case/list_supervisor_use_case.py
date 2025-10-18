from core.kernel.result import Result
from infrastructure.repositories.supervisor_repository import SupervisorRepository

class ListSupervisorUseCase:
    def __init__(self, supervisor_repository: SupervisorRepository):
        self.supervisor_repository = supervisor_repository

    async def execute(self):
        try:
            supervisors = await self.supervisor_repository.list_all()
            return Result.ok(supervisors)
        except Exception as e:
            return Result.error(f"Erro ao listar supervisores")
