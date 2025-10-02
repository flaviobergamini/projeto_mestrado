from datetime import datetime
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.models.users import User
from infrastructure.repositories.user_repository import UserRepository

class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(self, user: User):
        try:
            check_user = await self.user_repository.get_by_email(user.email)

            if check_user:
                return Result.bad_request("E-mail já cadastrado")
            
            user.password = self.jwt_service.hash_password(user.password)
            user.created_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()

            await self.user_repository.add(user)

            check_user = await self.user_repository.get_by_email(user.email)
            
            if check_user:
                token = self.jwt_service.create_access_token({"sub": str(check_user.id)})
                return Result.ok({"access_token": token})

            return Result.error(f"Erro ao cadastrar usuário no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar usuário")