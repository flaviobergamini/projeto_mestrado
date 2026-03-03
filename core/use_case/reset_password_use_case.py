from datetime import datetime
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class ResetPasswordUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(self, token: str, new_password: str):
        try:
            # Verificar se o token é válido
            payload = self.jwt_service.decode_token(token)
            if not payload:
                return Result.bad_request("Token inválido ou expirado")

            # Verificar o tipo do token
            token_type = payload.get("type")
            if token_type != "reset":
                return Result.bad_request("Token inválido")

            user_id = payload.get("sub")
            if not user_id:
                return Result.bad_request("Token inválido")

            # Buscar usuário pelo ID
            user = await self.user_repository.get_by_id(int(user_id))
            if not user:
                return Result.not_found("Usuário não encontrado")

            # Verificar se o token corresponde ao salvo no banco
            if user.reset_token != token:
                return Result.bad_request("Token inválido ou já utilizado")

            # Verificar se o token não expirou (verificação adicional além do JWT)
            if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
                return Result.bad_request("Token expirado")

            # Validar nova senha
            if len(new_password) < 6:
                return Result.bad_request("A senha deve ter no mínimo 6 caracteres")

            # Atualizar senha e limpar tokens de reset
            user.password = self.jwt_service.hash_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            user.updated_at = datetime.utcnow()

            await self.user_repository.update(user)

            return Result.ok({
                "message": "Senha redefinida com sucesso"
            })

        except Exception as e:
            logger.error(f"Erro ao redefinir senha: {str(e)}")
            return Result.error("Erro ao redefinir senha")
