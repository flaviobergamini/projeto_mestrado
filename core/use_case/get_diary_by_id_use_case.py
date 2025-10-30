from core.kernel.result import Result
from infrastructure.repositories.diary_repository import DiaryRepository


class GetDiaryByIdUseCase:
    """
    Caso de uso para buscar um registro diário específico por ID.
    """

    def __init__(self, diary_repository: DiaryRepository):
        self.diary_repository = diary_repository

    async def execute(self, diary_id: int):
        try:
            diary = await self.diary_repository.get_by_id(diary_id)

            if not diary:
                return Result.not_found("Registro diário não encontrado")

            return Result.ok(diary)
        except Exception as e:
            return Result.error(f"Erro ao buscar registro diário: {str(e)}")
