from core.kernel.result import Result
from infrastructure.models.school import School
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository


class DeleteBeneficiaryUseCase:
    def __init__(self, beneficiary_repository: BeneficiaryRepository):
        self.beneficiary_repository = beneficiary_repository

    async def execute(self, beneficiary_id: int):
        try:
            existing_beneficiary = await self.beneficiary_repository.get_by_id(beneficiary_id)
            
            if not existing_beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            await self.beneficiary_repository.delete(existing_beneficiary)

            return Result.ok(existing_beneficiary)
        except Exception as e:
            return Result.error(f"Erro ao deletar beneficiário: {str(e)}")