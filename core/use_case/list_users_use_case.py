import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository

logger = logging.getLogger(__name__)


class ListUsersUseCase:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self):
        try:
            users = await self.user_repository.get_all()
            return Result.ok(users)
        except Exception as e:
            logger.error(f"Erro ao listar usuários: {e}")
            return Result.error("Erro ao listar usuários")
