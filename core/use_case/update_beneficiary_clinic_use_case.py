from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.beneficiary_clinic import BeneficiaryClinic
from infrastructure.repositories.beneficiary_clinic_repository import BeneficiaryClinicRepository

class UpdateBeneficiaryClinicUseCase:
    def __init__(self, beneficiary_clinic_repository: BeneficiaryClinicRepository):
        self.beneficiary_clinic_repository = beneficiary_clinic_repository

    async def execute(self, beneficiary_clinic: BeneficiaryClinic):
        try:
            check_beneficiary_clinic = await self.beneficiary_clinic_repository.get_by_id(beneficiary_clinic.id)

            if not check_beneficiary_clinic:
                return Result.not_found("Relacionamento beneficiário-clínica não encontrado")

            beneficiary_clinic.updated_at = datetime.utcnow()

            updated_beneficiary_clinic = await self.beneficiary_clinic_repository.update(beneficiary_clinic)

            return Result.ok(updated_beneficiary_clinic)
        except Exception as e:
            return Result.error(f"Erro ao atualizar relacionamento beneficiário-clínica")
