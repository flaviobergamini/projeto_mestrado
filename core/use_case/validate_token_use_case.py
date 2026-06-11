import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException

logger = logging.getLogger(__name__)


class ValidateTokenUseCase:
    """
    Valida o token Cognito e retorna o perfil completo do usuário
    buscado no banco — incluindo os campos de escopo (municipality_id,
    school_id, teacher_id) necessários para filtrar dados nas rotas.

    O JWT carrega apenas sub + role. Os dados de escopo nunca ficam
    no token; são sempre buscados da tabela user_profiles.
    """

    def __init__(self, auth_service: IAuthService, user_repository: IUserRepository):
        self.auth_service = auth_service
        self.user_repository = user_repository

    async def execute(self, access_token: str):
        try:
            # get_username_from_token retorna o 'sub' (UUID estável do Cognito)
            # que corresponde ao campo 'id' em user_profiles
            cognito_sub = self.auth_service.get_username_from_token(access_token)
        except AuthException as e:
            return Result.unauthorized(e.message)

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
            "teacher_id":      user["teacher_id"],
            "is_active":       user["is_active"],
        })
