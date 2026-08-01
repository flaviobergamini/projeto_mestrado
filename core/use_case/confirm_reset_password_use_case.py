import logging
from core.kernel.result import Result
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException

logger = logging.getLogger(__name__)


class ConfirmResetPasswordUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    async def execute(self, username: str, code: str, new_password: str):
        try:
            self.auth_service.confirm_forgot_password(username, code, new_password)
            return Result.ok({"message": "Senha redefinida com sucesso."})
        except AuthException as e:
            return Result.bad_request(e.message)
        except Exception as e:
            logger.error(f"Erro ao redefinir senha: {e}")
            return Result.error("Erro ao redefinir senha")
