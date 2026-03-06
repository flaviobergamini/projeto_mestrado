from core.kernel.result import Result
from infrastructure.services.supabase_auth_service import SupabaseAuthService
import logging

logger = logging.getLogger(__name__)


class ResetPasswordUseCase:
    def __init__(self, supabase_auth_service: SupabaseAuthService):
        self.supabase_auth_service = supabase_auth_service

    async def execute(self, access_token: str, refresh_token: str, new_password: str):
        try:
            if len(new_password) < 6:
                return Result.bad_request("A senha deve ter no mínimo 6 caracteres")

            try:
                self.supabase_auth_service.update_password(access_token, refresh_token, new_password)
            except Exception as e:
                error_msg = str(e).lower()
                if "invalid" in error_msg or "expired" in error_msg:
                    return Result.bad_request("Token inválido ou expirado")
                logger.error(f"Erro ao redefinir senha no Supabase: {str(e)}")
                return Result.error("Erro ao redefinir senha")

            return Result.ok({"message": "Senha redefinida com sucesso"})

        except Exception as e:
            logger.error(f"Erro ao redefinir senha: {str(e)}")
            return Result.error("Erro ao redefinir senha")
