from core.kernel.result import Result
from infrastructure.repositories.school_repository import SchoolRepository


class GetSchoolByIdUseCase:
    def __init__(self, school_repository: SchoolRepository):
        self.school_repository = school_repository

    async def execute(self, school_id: int):
        try:
            school = await self.school_repository.get_by_id(school_id)
            if not school:
                return Result.not_found("Escola não encontrada")
            return Result.ok(school)
        except Exception as e:
            return Result.error(f"Erro ao obter escola por ID")