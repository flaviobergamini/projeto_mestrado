import logging
from core.kernel.result import Result
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException

logger = logging.getLogger(__name__)


class ForgotPasswordUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    async def execute(self, username: str):
        try:
            self.auth_service.forgot_password(username)
            return Result.ok({"message": "Código de redefinição enviado para o e-mail cadastrado."})
        except AuthException as e:
            return Result.bad_request(e.message)
        except Exception as e:
            logger.error(f"Erro ao solicitar redefinição de senha: {e}")
            return Result.error("Erro ao solicitar redefinição de senha")
