from core.kernel.result import Result
from infrastructure.repositories.diary_repository import DiaryRepository


class UpdateDiaryUseCase:
    """
    Caso de uso para atualizar um registro diário existente.
    """

    def __init__(self, diary_repository: DiaryRepository):
        self.diary_repository = diary_repository

    async def execute(self, diary_id: int, **kwargs):
        try:
            # Verificar se o registro existe
            existing_diary = await self.diary_repository.get_by_id(diary_id)
            if not existing_diary:
                return Result.not_found("Registro diário não encontrado")

            # Atualizar o registro
            updated_diary = await self.diary_repository.update(diary_id, **kwargs)

            if not updated_diary:
                return Result.error("Erro ao atualizar registro diário")

            return Result.ok(updated_diary)
        except Exception as e:
            return Result.error(f"Erro ao atualizar registro diário: {str(e)}")
