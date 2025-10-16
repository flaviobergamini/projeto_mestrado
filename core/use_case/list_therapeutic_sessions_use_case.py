from core.kernel.result import Result
from infrastructure.repositories.therapeutic_sessions_repository import TherapeuticSessionsRepository

class ListTherapeuticSessionsUseCase:
    def __init__(self, therapeutic_sessions_repository: TherapeuticSessionsRepository):
        self.therapeutic_sessions_repository = therapeutic_sessions_repository

    async def execute(self):
        try:
            therapeutic_sessions = await self.therapeutic_sessions_repository.list_all()
            return Result.ok(therapeutic_sessions)
        except Exception as e:
            return Result.error(f"Erro ao listar sessões terapêuticas")
