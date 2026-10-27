import logging
from typing import Optional
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository
import uuid
from core.services.jwt_service import JwtService
from core.permissions.roles import CAN_CREATE_USER, ALL_ROLES

logger = logging.getLogger(__name__)


class CreateUserUseCase:
    def __init__(self, user_repository: IUserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt = jwt_service

    async def execute(
        self,
        requester_role: str,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str],
        role: str,
        municipality_id: Optional[str] = None,
        school_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
        school_ids: Optional[list[str]] = None,
    ):
        try:
            if requester_role not in CAN_CREATE_USER:
                return Result.unauthorized("Apenas administradores podem cadastrar usuários")

            if role not in ALL_ROLES:
                return Result.bad_request(f"Role inválido. Valores aceitos: {', '.join(ALL_ROLES)}")

            existing = await self.user_repository.get_by_username(username)
            if existing:
                return Result.bad_request("Nome de usuário já cadastrado")

            cognito_sub = str(uuid.uuid4())

            await self.user_repository.add(
                id=cognito_sub,
                username=username,
                full_name=full_name,
                role=role,
                municipality_id=municipality_id,
                school_id=school_id,
                school_ids=school_ids,
                teacher_id=teacher_id,
            )
            await self.user_repository.set_password_hash(cognito_sub, self.jwt.hash_password(password))

            return Result.ok({
                "message": "Usuário criado com sucesso. ",
                "username": username,
                "user_id": cognito_sub,
            })

        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {e}")
            return Result.error("Erro ao cadastrar usuário")
