from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class RefreshTokenUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(self, refresh_token: str):
        try:
            # Verificar se o token é válido
            payload = self.jwt_service.decode_token(refresh_token)
            if not payload:
                return Result.unauthorized("Refresh token inválido ou expirado")

            # Verificar o tipo do token
            token_type = payload.get("type")
            if token_type != "refresh":
                return Result.unauthorized("Token inválido")

            user_id = payload.get("sub")
            if not user_id:
                return Result.unauthorized("Token inválido")

            # Verificar se o usuário existe
            user = await self.user_repository.get_by_id(int(user_id))
            if not user:
                return Result.not_found("Usuário não encontrado")

            # Gerar novos tokens
            new_access_token = self.jwt_service.create_access_token({"sub": str(user.id)})
            new_refresh_token = self.jwt_service.create_refresh_token({"sub": str(user.id)})

            return Result.ok({
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "email_verified": user.email_verified
            })

        except Exception as e:
            logger.error(f"Erro ao renovar token: {str(e)}")
            return Result.error("Erro ao renovar token")
