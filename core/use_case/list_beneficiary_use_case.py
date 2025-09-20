from core.kernel.result import Result
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository


class ListBeneficiaryUseCase:
    def __init__(self, beneficiary_repository: BeneficiaryRepository):
        self.beneficiary_repository = beneficiary_repository
    
    async def execute(self):
        try:
            beneficiaries = await self.beneficiary_repository.list_all()
            return Result.ok(beneficiaries)
        except Exception as e:
            return Result.error(f"Erro ao listar beneficiários")