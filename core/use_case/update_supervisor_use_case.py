from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.supervisor import Supervisor
from infrastructure.repositories.supervisor_repository import SupervisorRepository

class UpdateSupervisorUseCase:
    def __init__(self, supervisor_repository: SupervisorRepository):
        self.supervisor_repository = supervisor_repository

    async def execute(self, supervisor: Supervisor):
        try:
            check_supervisor = await self.supervisor_repository.get_by_id(supervisor.id)

            if not check_supervisor:
                return Result.not_found("Supervisor não encontrado")

            supervisor.updated_at = datetime.utcnow()

            updated_supervisor = await self.supervisor_repository.update(supervisor)

            return Result.ok(updated_supervisor)
        except Exception as e:
            return Result.error(f"Erro ao atualizar supervisor")
