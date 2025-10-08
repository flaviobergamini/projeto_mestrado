from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.beneficiary import Beneficiary
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository

class CreateBeneficiaryUseCase:
    def __init__(self, beneficiary_repository: BeneficiaryRepository):
        self.beneficiary_repository = beneficiary_repository

    async def execute(self, beneficiary: Beneficiary):
        try:
            check_beneficiary = await self.beneficiary_repository.verify(beneficiary)

            if check_beneficiary:
                return Result.bad_request("Beneficiário já cadastrado")
            
            beneficiary.created_at = datetime.utcnow()
            beneficiary.updated_at = datetime.utcnow()

            await self.beneficiary_repository.add(beneficiary)

            check_beneficiary = await self.beneficiary_repository.verify(beneficiary)
            
            if check_beneficiary:
                return Result.ok(check_beneficiary)

            return Result.error(f"Erro ao cadastrar beneficiário no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar beneficiário")