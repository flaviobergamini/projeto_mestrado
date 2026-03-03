from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.models.users import User
from infrastructure.repositories.user_repository import UserRepository


class LoginUserUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(self, email: str, password: str):
        try:
            user = await self.user_repository.get_by_email(email)

            if not user:
                return Result.not_found("Usuário não encontrado")
            
            check_password = self.jwt_service.verify_password(password, user.password)

            if not check_password:
                return Result.unauthorized("Senha inválida")

            token = self.jwt_service.create_access_token({"sub": str(user.id)})
            refresh_token = self.jwt_service.create_refresh_token({"sub": str(user.id)})

            return Result.ok({
                "access_token": token,
                "refresh_token": refresh_token,
                "email_verified": user.email_verified
            })

        except Exception as e:
            return Result.error(f"Erro ao buscar usuário: {e}")