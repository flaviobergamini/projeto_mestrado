from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.therapeutic_sessions import TherapeuticSessions
from infrastructure.repositories.therapeutic_sessions_repository import TherapeuticSessionsRepository

class CreateTherapeuticSessionsUseCase:
    def __init__(self, therapeutic_sessions_repository: TherapeuticSessionsRepository):
        self.therapeutic_sessions_repository = therapeutic_sessions_repository

    async def execute(self, therapeutic_sessions: TherapeuticSessions):
        try:
            check_therapeutic_sessions = await self.therapeutic_sessions_repository.verify(therapeutic_sessions)

            if check_therapeutic_sessions:
                return Result.bad_request("Sessão terapêutica já cadastrada")

            therapeutic_sessions.created_at = datetime.utcnow()
            therapeutic_sessions.updated_at = datetime.utcnow()

            await self.therapeutic_sessions_repository.add(therapeutic_sessions)

            check_therapeutic_sessions = await self.therapeutic_sessions_repository.verify(therapeutic_sessions)

            if check_therapeutic_sessions:
                return Result.ok(check_therapeutic_sessions)

            return Result.error(f"Erro ao cadastrar sessão terapêutica no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar sessão terapêutica")
