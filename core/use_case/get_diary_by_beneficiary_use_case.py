from core.kernel.result import Result
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository


class GetDiaryByBeneficiaryUseCase:
    """
    Caso de uso para buscar todos os registros diários de um beneficiário específico.
    Útil para análise de padrões comportamentais ao longo do tempo.
    """

    def __init__(
        self,
        diary_repository: DiaryRepository,
        beneficiary_repository: BeneficiaryRepository,
    ):
        self.diary_repository = diary_repository
        self.beneficiary_repository = beneficiary_repository

    async def execute(self, beneficiary_id: int):
        try:
            # Verificar se o beneficiário existe
            beneficiary = await self.beneficiary_repository.get_by_id(beneficiary_id)
            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            # Buscar todos os registros diários do beneficiário
            diaries = await self.diary_repository.get_by_beneficiary(beneficiary_id)

            return Result.ok(diaries)
        except Exception as e:
            return Result.error(
                f"Erro ao buscar registros diários do beneficiário: {str(e)}"
            )
