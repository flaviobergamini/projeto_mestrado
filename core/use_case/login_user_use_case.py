from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.services.supabase_auth_service import SupabaseAuthService
import logging

logger = logging.getLogger(__name__)


class LoginUserUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService, supabase_auth_service: SupabaseAuthService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service
        self.supabase_auth_service = supabase_auth_service

    async def execute(self, email: str, password: str):
        try:
            try:
                response = self.supabase_auth_service.sign_in(email, password)
            except Exception as e:
                error_msg = str(e).lower()
                if "invalid login credentials" in error_msg or "invalid credentials" in error_msg:
                    return Result.unauthorized("Email ou senha inválidos")
                if "email not confirmed" in error_msg:
                    return Result.unauthorized("Email não confirmado. Verifique sua caixa de entrada.")
                logger.error(f"Erro ao autenticar no Supabase: {str(e)}")
                return Result.error("Erro ao autenticar usuário")

            if not response.user:
                return Result.unauthorized("Email ou senha inválidos")

            user = await self.user_repository.get_by_email(email)
            if not user:
                return Result.not_found("Usuário não encontrado")

            role = user.role.value if user.role else "teacher"
            token = self.jwt_service.create_access_token({"sub": str(user.id), "role": role})
            refresh_token = self.jwt_service.create_refresh_token({"sub": str(user.id), "role": role})

            email_verified = response.user.email_confirmed_at is not None

            return Result.ok({
                "access_token": token,
                "refresh_token": refresh_token,
                "email_verified": email_verified,
                "role": role,
                "name": user.name,
                "user_id": user.id,
            })

        except Exception as e:
            logger.error(f"Erro ao fazer login: {str(e)}")
            return Result.error("Erro ao autenticar usuário")
