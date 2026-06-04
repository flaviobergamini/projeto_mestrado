import logging
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(self, refresh_token: str):
        try:
            payload = self.jwt_service.decode_token(refresh_token)
            if not payload:
                return Result.unauthorized("Refresh token inválido ou expirado")

            if payload.get("type") != "refresh":
                return Result.unauthorized("Token inválido")

            user_id = payload.get("sub")
            if not user_id:
                return Result.unauthorized("Token inválido")

            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return Result.not_found("Usuário não encontrado")

            if not user.is_active:
                return Result.unauthorized("Usuário inativo")

            access_token = self.jwt_service.create_access_token(
                {"sub": user.id, "role": user.role, "username": user.username}
            )
            new_refresh_token = self.jwt_service.create_refresh_token(
                {"sub": user.id, "role": user.role, "username": user.username}
            )

            return Result.ok({
                "access_token": access_token,
                "refresh_token": new_refresh_token,
            })

        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            return Result.error("Erro ao renovar token")
