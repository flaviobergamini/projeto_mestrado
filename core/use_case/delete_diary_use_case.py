from core.kernel.result import Result
from infrastructure.repositories.diary_repository import DiaryRepository


class DeleteDiaryUseCase:
    """
    Caso de uso para deletar um registro diário.
    """

    def __init__(self, diary_repository: DiaryRepository):
        self.diary_repository = diary_repository

    async def execute(self, diary_id: int):
        try:
            # Verificar se o registro existe
            diary = await self.diary_repository.get_by_id(diary_id)
            if not diary:
                return Result.not_found("Registro diário não encontrado")

            # Deletar o registro
            deleted = await self.diary_repository.delete(diary_id)

            if not deleted:
                return Result.error("Erro ao deletar registro diário")

            return Result.ok({"message": "Registro diário deletado com sucesso"})
        except Exception as e:
            return Result.error(f"Erro ao deletar registro diário: {str(e)}")
