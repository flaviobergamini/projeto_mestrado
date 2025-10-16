from core.kernel.result import Result
from infrastructure.repositories.therapeutic_sessions_repository import TherapeuticSessionsRepository

class DeleteTherapeuticSessionsUseCase:
    def __init__(self, therapeutic_sessions_repository: TherapeuticSessionsRepository):
        self.therapeutic_sessions_repository = therapeutic_sessions_repository

    async def execute(self, therapeutic_sessions_id: int):
        try:
            therapeutic_sessions = await self.therapeutic_sessions_repository.get_by_id(therapeutic_sessions_id)

            if not therapeutic_sessions:
                return Result.not_found("Sessão terapêutica não encontrada")

            await self.therapeutic_sessions_repository.delete(therapeutic_sessions)

            return Result.ok("Sessão terapêutica deletada com sucesso")
        except Exception as e:
            return Result.error(f"Erro ao deletar sessão terapêutica")
