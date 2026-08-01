import logging
from core.kernel.result import Result
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException

logger = logging.getLogger(__name__)


class ConfirmEmailUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    async def execute(self, username: str, code: str):
        try:
            self.auth_service.confirm_sign_up(username, code)
            return Result.ok({"message": "E-mail confirmado com sucesso. Você já pode fazer login."})
        except AuthException as e:
            return Result.bad_request(e.message)
        except Exception as e:
            logger.error(f"Erro ao confirmar e-mail: {e}")
            return Result.error("Erro ao confirmar e-mail")
