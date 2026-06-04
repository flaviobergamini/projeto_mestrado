import uuid
import logging
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.models.user_profile import UserProfile
from infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    async def execute(
        self,
        username: str,
        password: str,
        full_name: str | None,
        role: str,
        municipality_id: str | None = None,
        school_id: str | None = None,
        teacher_id: str | None = None,
    ):
        try:
            existing = await self.user_repository.get_by_username(username)
            if existing:
                return Result.bad_request("Nome de usuário já cadastrado")

            password_hash = self.jwt_service.hash_password(password)

            user = UserProfile(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
                municipality_id=municipality_id,
                school_id=school_id,
                teacher_id=teacher_id,
                is_active=True,
            )

            new_user = await self.user_repository.add(user)

            access_token = self.jwt_service.create_access_token(
                {"sub": new_user.id, "role": new_user.role, "username": new_user.username}
            )
            refresh_token = self.jwt_service.create_refresh_token(
                {"sub": new_user.id, "role": new_user.role, "username": new_user.username}
            )

            return Result.ok({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": new_user.id,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role": new_user.role,
            })

        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {e}")
            return Result.error("Erro ao cadastrar usuário")
