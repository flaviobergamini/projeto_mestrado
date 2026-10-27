import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.services.jwt_service import JwtService

logger = logging.getLogger(__name__)


class ValidateTokenUseCase:
    """
    Valida o token Cognito e retorna o perfil completo do usuário
    buscado no banco — incluindo os campos de escopo (municipality_id,
    school_id, teacher_id) necessários para filtrar dados nas rotas.

    O JWT carrega apenas sub + role. Os dados de escopo nunca ficam
    no token; são sempre buscados da tabela user_profiles.
    """

    def __init__(self, jwt_service: JwtService, user_repository: IUserRepository):
        self.jwt = jwt_service
        self.user_repository = user_repository

    async def execute(self, access_token: str):
        payload = self.jwt.decode_token(access_token)
        if not payload or payload.get("type") != "access" or not payload.get("sub"):
            return Result.unauthorized("Token inválido ou expirado")
        cognito_sub = payload["sub"]

        user = await self.user_repository.get_by_id(cognito_sub)
        if not user:
            return Result.not_found("Usuário não encontrado")

        if not user["is_active"]:
            return Result.unauthorized("Usuário inativo")

        # Retorna o perfil completo — usado para construir o escopo
        # nos use cases sem nenhuma chamada adicional ao banco
        return Result.ok({
            "user_id":         user["id"],
            "username":        user["username"],
            "full_name":       user["full_name"],
            "role":            user["role"],
            "municipality_id": user["municipality_id"],
            "school_id":       user["school_id"],
            "school_ids":      user.get("school_ids", []),
            "teacher_id":      user["teacher_id"],
            "is_active":       user["is_active"],
        })
