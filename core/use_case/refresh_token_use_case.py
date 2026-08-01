import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    def __init__(self, user_repository: IUserRepository, auth_service: IAuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service

    async def execute(self, username: str, refresh_token: str):
        try:
            try:
                tokens = self.auth_service.refresh_token(username, refresh_token)
            except AuthException as e:
                return Result.unauthorized(e.message)

            user = await self.user_repository.get_by_username(username)
            if not user:
                return Result.not_found("Usuário não encontrado")

            return Result.ok({
                **tokens,
                "user_id": user["id"],
                "username": user["username"],
                "role": user["role"],
            })

        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            return Result.error("Erro ao renovar token")
