import logging
from core.kernel.result import Result
from core.interfaces.i_user_repository import IUserRepository

logger = logging.getLogger(__name__)


class UpdateUserRoleUseCase:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, role: str):
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return Result.not_found("Usuário não encontrado")

            updated = await self.user_repository.update_role(user_id, role)
            return Result.ok(updated)
        except Exception as e:
            logger.error(f"Erro ao atualizar role: {e}")
            return Result.error("Erro ao atualizar role do usuário")
