import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.services.jwt_service import JwtService

logger = logging.getLogger(__name__)

ACCESS_MINUTES = 60
REFRESH_MINUTES = 60 * 24 * 7


def issue_tokens(jwt: JwtService, user: dict) -> dict:
    claims = {"sub": user["id"], "role": user["role"], "username": user["username"]}
    return {
        "access_token": jwt.create_access_token(claims, ACCESS_MINUTES),
        "id_token": jwt.create_access_token(claims, ACCESS_MINUTES),
        "refresh_token": jwt.create_refresh_token(claims, REFRESH_MINUTES),
        "expires_in": ACCESS_MINUTES * 60,
    }


class LoginUserUseCase:
    """Login local (sem Cognito): e-mail ou nome de usuário + senha verificada contra o hash no banco."""

    def __init__(self, user_repository: IUserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt = jwt_service

    async def execute(self, identifier: str, password: str):
        try:
            user = await self.user_repository.find_by_login(identifier)
            stored = await self.user_repository.get_password_hash(user["id"]) if user else None
            if not user or not stored or not self.jwt.verify_password(password, stored):
                return Result.unauthorized("Usuário ou senha inválidos")
            if not user["is_active"]:
                return Result.unauthorized("Usuário inativo")
            return Result.ok({
                **issue_tokens(self.jwt, user),
                "user_id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"],
            })
        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}")
            return Result.error("Erro ao autenticar usuário")
