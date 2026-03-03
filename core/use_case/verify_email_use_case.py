from datetime import datetime
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class VerifyEmailUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(self, token: str):
        try:
            # Verificar se o token é válido
            payload = self.jwt_service.decode_token(token)
            if not payload:
                return Result.bad_request("Token inválido ou expirado")

            # Verificar o tipo do token
            token_type = payload.get("type")
            if token_type != "verification":
                return Result.bad_request("Token inválido")

            email = payload.get("email")
            if not email:
                return Result.bad_request("Token inválido")

            # Buscar usuário pelo email
            user = await self.user_repository.get_by_email(email)
            if not user:
                return Result.not_found("Usuário não encontrado")

            # Verificar se o token corresponde ao salvo no banco
            if user.verification_token != token:
                return Result.bad_request("Token inválido")

            # Verificar se o email já foi verificado
            if user.email_verified:
                return Result.bad_request("Email já verificado")

            # Marcar email como verificado e limpar o token
            user.email_verified = True
            user.verification_token = None
            user.updated_at = datetime.utcnow()

            await self.user_repository.update(user)

            return Result.ok({
                "message": "Email verificado com sucesso",
                "email_verified": True
            })

        except Exception as e:
            logger.error(f"Erro ao verificar email: {str(e)}")
            return Result.error("Erro ao verificar email")
