from datetime import datetime
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.models.users import User
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.services.supabase_auth_service import SupabaseAuthService
import logging

logger = logging.getLogger(__name__)

SUPABASE_MANAGED = "SUPABASE_MANAGED"


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService, supabase_auth_service: SupabaseAuthService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service
        self.supabase_auth_service = supabase_auth_service

    async def execute(self, user: User):
        try:
            check_user = await self.user_repository.get_by_email(user.email)
            if check_user:
                return Result.bad_request("E-mail já cadastrado")

            try:
                response = self.supabase_auth_service.sign_up(user.email, user.password, user.name)
            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"Erro ao cadastrar usuário no Supabase: {str(e)}")
                if "invalid" in error_msg or "validation" in error_msg:
                    return Result.bad_request("E-mail inválido")
                if "already registered" in error_msg or "already exists" in error_msg:
                    return Result.bad_request("E-mail já cadastrado")
                return Result.error("Erro ao cadastrar usuário")

            if not response.user:
                return Result.error("Erro ao cadastrar usuário")

            user.password = SUPABASE_MANAGED
            user.created_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            user.email_verified = False

            new_user = await self.user_repository.add(user)

            token = self.jwt_service.create_access_token({"sub": str(new_user.id)})
            refresh_token = self.jwt_service.create_refresh_token({"sub": str(new_user.id)})

            return Result.ok({
                "access_token": token,
                "refresh_token": refresh_token,
                "email_verified": False,
                "message": "Usuário criado com sucesso. Verifique seu email para ativar sua conta."
            })

        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {str(e)}")
            return Result.error("Erro ao cadastrar usuário")
