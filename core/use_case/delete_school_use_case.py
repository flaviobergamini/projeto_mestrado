from core.kernel.result import Result
from infrastructure.models.school import School
from infrastructure.repositories.school_repository import SchoolRepository


class DeleteSchoolUseCase:
    def __init__(self, school_repository: SchoolRepository):
        self.school_repository = school_repository

    async def execute(self, school_id: int):
        try:
            existing_school = await self.school_repository.get_by_id(school_id)
            
            if not existing_school:
                return Result.not_found("Escola não encontrada")

            await self.school_repository.delete(existing_school)

            return Result.ok(existing_school)
        except Exception as e:
            return Result.error(f"Erro ao deletar escola: {str(e)}")