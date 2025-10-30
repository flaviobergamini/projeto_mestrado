from core.kernel.result import Result
from infrastructure.repositories.diary_repository import DiaryRepository


class ListDiaryUseCase:
    """
    Caso de uso para listar todos os registros diários.
    """

    def __init__(self, diary_repository: DiaryRepository):
        self.diary_repository = diary_repository

    async def execute(self):
        try:
            diaries = await self.diary_repository.list_all()
            return Result.ok(diaries)
        except Exception as e:
            return Result.error(f"Erro ao listar registros diários: {str(e)}")
