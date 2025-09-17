from core.kernel.result import Result
from infrastructure.models.school import School
from infrastructure.repositories.school_repository import SchoolRepository


class UpdateSchoolUseCase:
    def __init__(self, school_repository: SchoolRepository):
        self.school_repository = school_repository

    async def execute(self, school: School):
        try:
            existing_school = await self.school_repository.get_by_id(school.id)
            
            if not existing_school:
                return Result.not_found("Escola não encontrada")

            updated_school = await self.school_repository.update(school)

            return Result.ok(updated_school)
        except Exception as e:
            return Result.error(f"Erro ao atualizar escola: {str(e)}")