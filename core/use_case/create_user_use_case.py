import logging
from typing import Optional
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import AuthException, UserAlreadyExistsError

logger = logging.getLogger(__name__)


class CreateUserUseCase:
    def __init__(self, user_repository: IUserRepository, auth_service: IAuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service

    async def execute(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str],
        role: str,
        municipality_id: Optional[str] = None,
        school_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
    ):
        try:
            existing = await self.user_repository.get_by_username(username)
            if existing:
                return Result.bad_request("Nome de usuário já cadastrado")

            try:
                cognito_sub = self.auth_service.sign_up(username, password, email, full_name)
            except UserAlreadyExistsError as e:
                return Result.bad_request(e.message)
            except AuthException as e:
                return Result.bad_request(e.message)

            await self.user_repository.add(
                id=cognito_sub,
                username=username,
                full_name=full_name,
                role=role,
                municipality_id=municipality_id,
                school_id=school_id,
                teacher_id=teacher_id,
            )

            return Result.ok({
                "message": "Usuário criado. Verifique seu e-mail para confirmar o cadastro.",
                "username": username,
                "user_id": cognito_sub,
            })

        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {e}")
            return Result.error("Erro ao cadastrar usuário")
