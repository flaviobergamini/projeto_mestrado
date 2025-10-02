from core.kernel.result import Result
from infrastructure.repositories.school_repository import SchoolRepository


class ListSchoolUseCase:
    def __init__(self, school_repository: SchoolRepository):
        self.school_repository = school_repository

    async def execute(self):
        try:
            schools = await self.school_repository.list_all()
            return Result.ok(schools)
        except Exception as e:
            return Result.error(f"Erro ao listar escolas")