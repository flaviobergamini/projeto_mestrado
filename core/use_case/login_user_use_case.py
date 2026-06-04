import logging
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class LoginUserUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(self, username: str, password: str):
        try:
            user = await self.user_repository.get_by_username(username)
            if not user:
                return Result.unauthorized("Usuário ou senha inválidos")

            if not user.is_active:
                return Result.unauthorized("Usuário inativo")

            if not self.jwt_service.verify_password(password, user.password_hash):
                return Result.unauthorized("Usuário ou senha inválidos")

            access_token = self.jwt_service.create_access_token(
                {"sub": user.id, "role": user.role, "username": user.username}
            )
            refresh_token = self.jwt_service.create_refresh_token(
                {"sub": user.id, "role": user.role, "username": user.username}
            )

            return Result.ok({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
            })

        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}")
            return Result.error("Erro ao autenticar usuário")
