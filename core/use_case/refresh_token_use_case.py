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
            user = await self.user_repository.get_by_username(username)
            if not user:
                return Result.not_found("Usuário não encontrado")

            try:
                # O SECRET_HASH do fluxo REFRESH_TOKEN_AUTH é verificado pelo
                # Cognito contra o Username CANÔNICO (o sub — um UUID), não
                # contra o e-mail, mesmo num pool com UsernameAttributes=email.
                # USER_PASSWORD_AUTH (login) aceita e-mail como alias e valida
                # o SECRET_HASH computado com ele, mas REFRESH_TOKEN_AUTH não —
                # sempre falha com "Unable to verify secret hash" se passarmos
                # o e-mail aqui. user["id"] é o sub (ver CreateUserUseCase:
                # id=cognito_sub), então é isso que precisa ir pro SECRET_HASH.
                tokens = self.auth_service.refresh_token(user["id"], refresh_token)
            except AuthException as e:
                return Result.unauthorized(e.message)

            return Result.ok({
                **tokens,
                "user_id": user["id"],
                "username": user["username"],
                "role": user["role"],
            })

        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            return Result.error("Erro ao renovar token")
