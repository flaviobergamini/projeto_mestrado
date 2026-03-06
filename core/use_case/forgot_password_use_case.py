from core.kernel.result import Result
from infrastructure.services.supabase_auth_service import SupabaseAuthService
import logging

logger = logging.getLogger(__name__)


class ForgotPasswordUseCase:
    def __init__(self, supabase_auth_service: SupabaseAuthService):
        self.supabase_auth_service = supabase_auth_service

    async def execute(self, email: str):
        try:
            self.supabase_auth_service.reset_password_for_email(email)
        except Exception as e:
            logger.error(f"Erro ao enviar email de recuperação: {str(e)}")

        return Result.ok({
            "message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha."
        })
