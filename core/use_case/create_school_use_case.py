from datetime import datetime
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.models.school import School
from infrastructure.repositories.school_repository import SchoolRepository

class CreateSchoolUseCase:
    def __init__(self, school_repository: SchoolRepository, jwt_service: JwtService):
        self.school_repository = school_repository
        self.jwt_service = jwt_service

    async def execute(self, school: School):
        try:
            check_school = await self.school_repository.verify(school)

            if check_school:
                return Result.bad_request("Escola já cadastrada")
            
            school.created_at = datetime.utcnow()
            school.updated_at = datetime.utcnow()

            await self.school_repository.add(school)

            check_school = await self.school_repository.verify(school)
            
            if check_school:
                return Result.ok(check_school)

            return Result.error(f"Erro ao cadastrar escola no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar escola")