from core.kernel.result import Result
from infrastructure.models.beneficiary import Beneficiary
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository


class UpdateBeneficiaryUseCase:
    def __init__(self, beneficiary_repository: BeneficiaryRepository):
        self.beneficiary_repository = beneficiary_repository

    async def execute(self, beneficiary: Beneficiary):
        try:
            existing_beneficiary = await self.beneficiary_repository.get_by_id(beneficiary.id)
            
            if not existing_beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            updated_beneficiary = await self.beneficiary_repository.update(beneficiary)

            return Result.ok(updated_beneficiary)
        except Exception as e:
            return Result.error(f"Erro ao atualizar beneficiário: {str(e)}")