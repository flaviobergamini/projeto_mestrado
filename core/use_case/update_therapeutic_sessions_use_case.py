from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.therapeutic_sessions import TherapeuticSessions
from infrastructure.repositories.therapeutic_sessions_repository import TherapeuticSessionsRepository

class UpdateTherapeuticSessionsUseCase:
    def __init__(self, therapeutic_sessions_repository: TherapeuticSessionsRepository):
        self.therapeutic_sessions_repository = therapeutic_sessions_repository

    async def execute(self, therapeutic_sessions: TherapeuticSessions):
        try:
            check_therapeutic_sessions = await self.therapeutic_sessions_repository.get_by_id(therapeutic_sessions.id)

            if not check_therapeutic_sessions:
                return Result.not_found("Sessão terapêutica não encontrada")

            therapeutic_sessions.updated_at = datetime.utcnow()

            updated_therapeutic_sessions = await self.therapeutic_sessions_repository.update(therapeutic_sessions)

            return Result.ok(updated_therapeutic_sessions)
        except Exception as e:
            return Result.error(f"Erro ao atualizar sessão terapêutica")
