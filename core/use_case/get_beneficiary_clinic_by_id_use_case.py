from core.kernel.result import Result
from infrastructure.repositories.beneficiary_clinic_repository import BeneficiaryClinicRepository

class GetBeneficiaryClinicByIdUseCase:
    def __init__(self, beneficiary_clinic_repository: BeneficiaryClinicRepository):
        self.beneficiary_clinic_repository = beneficiary_clinic_repository

    async def execute(self, beneficiary_clinic_id: int):
        try:
            beneficiary_clinic = await self.beneficiary_clinic_repository.get_by_id(beneficiary_clinic_id)

            if not beneficiary_clinic:
                return Result.not_found("Relacionamento beneficiário-clínica não encontrado")

            return Result.ok(beneficiary_clinic)
        except Exception as e:
            return Result.error(f"Erro ao buscar relacionamento beneficiário-clínica")
