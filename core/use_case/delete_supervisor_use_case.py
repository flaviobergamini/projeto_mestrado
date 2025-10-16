from core.kernel.result import Result
from infrastructure.repositories.supervisor_repository import SupervisorRepository

class DeleteSupervisorUseCase:
    def __init__(self, supervisor_repository: SupervisorRepository):
        self.supervisor_repository = supervisor_repository

    async def execute(self, supervisor_id: int):
        try:
            supervisor = await self.supervisor_repository.get_by_id(supervisor_id)

            if not supervisor:
                return Result.not_found("Supervisor não encontrado")

            await self.supervisor_repository.delete(supervisor)

            return Result.ok("Supervisor deletado com sucesso")
        except Exception as e:
            return Result.error(f"Erro ao deletar supervisor")
