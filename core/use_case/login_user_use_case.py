import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException, UserNotConfirmedError, InvalidCredentialsError

logger = logging.getLogger(__name__)


class LoginUserUseCase:
    def __init__(self, user_repository: IUserRepository, auth_service: IAuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service

    async def execute(self, username: str, password: str):
        try:
            try:
                tokens = self.auth_service.sign_in(username, password)
            except UserNotConfirmedError as e:
                return Result.unauthorized(e.message)
            except InvalidCredentialsError as e:
                return Result.unauthorized(e.message)
            except AuthException as e:
                return Result.unauthorized(e.message)

            user = await self.user_repository.get_by_username(username)
            if not user:
                return Result.not_found("Perfil de usuário não encontrado")

            if not user["is_active"]:
                return Result.unauthorized("Usuário inativo")

            return Result.ok({
                **tokens,
                "user_id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"],
            })

        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}")
            return Result.error("Erro ao autenticar usuário")
