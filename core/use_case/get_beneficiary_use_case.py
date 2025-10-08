from core.kernel.result import Result
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository


class GetBeneficiaryByIdUseCase:
    def __init__(self, beneficiary_repository: BeneficiaryRepository):
        self.beneficiary_repository = beneficiary_repository

    async def execute(self, beneficiary_id: int):
        try:
            school = await self.beneficiary_repository.get_by_id(beneficiary_id)
            if not school:
                return Result.not_found("Beneficiário não encontrado")
            return Result.ok(school)
        except Exception as e:
            return Result.error(f"Erro ao obter beneficiário por ID")