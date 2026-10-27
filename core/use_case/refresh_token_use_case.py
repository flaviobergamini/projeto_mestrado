import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.services.jwt_service import JwtService
from core.use_case.login_user_use_case import issue_tokens

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    def __init__(self, user_repository: IUserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt = jwt_service

    async def execute(self, username: str, refresh_token: str):
        try:
            payload = self.jwt.decode_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return Result.unauthorized("Sessão expirada — faça login novamente")
            user = await self.user_repository.get_by_id(payload.get("sub"))
            if not user:
                return Result.not_found("Usuário não encontrado")
            if not user["is_active"]:
                return Result.unauthorized("Usuário inativo")
            tokens = issue_tokens(self.jwt, user)
            tokens.pop("refresh_token")
            return Result.ok({**tokens, "user_id": user["id"], "username": user["username"], "role": user["role"]})
        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            return Result.error("Erro ao renovar token")
