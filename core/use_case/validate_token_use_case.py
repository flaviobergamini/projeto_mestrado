import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException

logger = logging.getLogger(__name__)


class ValidateTokenUseCase:
    def __init__(self, auth_service: IAuthService, user_repository: IUserRepository):
        self.auth_service = auth_service
        self.user_repository = user_repository

    async def execute(self, access_token: str):
        try:
            username = self.auth_service.get_username_from_token(access_token)
        except AuthException as e:
            return Result.unauthorized(e.message)

        user = await self.user_repository.get_by_username(username)
        if not user:
            return Result.not_found("Usuário não encontrado")

        if not user["is_active"]:
            return Result.unauthorized("Usuário inativo")

        return Result.ok({
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
        })
