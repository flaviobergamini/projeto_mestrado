from core.kernel.result import Result
from infrastructure.repositories.supervisor_repository import SupervisorRepository

class GetSupervisorByIdUseCase:
    def __init__(self, supervisor_repository: SupervisorRepository):
        self.supervisor_repository = supervisor_repository

    async def execute(self, supervisor_id: int):
        try:
            supervisor = await self.supervisor_repository.get_by_id(supervisor_id)

            if not supervisor:
                return Result.not_found("Supervisor não encontrado")

            return Result.ok(supervisor)
        except Exception as e:
            return Result.error(f"Erro ao buscar supervisor")
