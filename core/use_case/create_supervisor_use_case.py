from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.supervisor import Supervisor
from infrastructure.repositories.supervisor_repository import SupervisorRepository

class CreateSupervisorUseCase:
    def __init__(self, supervisor_repository: SupervisorRepository):
        self.supervisor_repository = supervisor_repository

    async def execute(self, supervisor: Supervisor):
        try:
            check_supervisor = await self.supervisor_repository.verify(supervisor)

            if check_supervisor:
                return Result.bad_request("Supervisor já cadastrado")

            supervisor.created_at = datetime.utcnow()
            supervisor.updated_at = datetime.utcnow()

            await self.supervisor_repository.add(supervisor)

            check_supervisor = await self.supervisor_repository.verify(supervisor)

            if check_supervisor:
                return Result.ok(check_supervisor)

            return Result.error(f"Erro ao cadastrar supervisor no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar supervisor")
