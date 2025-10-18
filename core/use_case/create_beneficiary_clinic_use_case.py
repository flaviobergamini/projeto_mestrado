from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.beneficiary_clinic import BeneficiaryClinic
from infrastructure.repositories.beneficiary_clinic_repository import BeneficiaryClinicRepository

class CreateBeneficiaryClinicUseCase:
    def __init__(self, beneficiary_clinic_repository: BeneficiaryClinicRepository):
        self.beneficiary_clinic_repository = beneficiary_clinic_repository

    async def execute(self, beneficiary_clinic: BeneficiaryClinic):
        try:
            check_beneficiary_clinic = await self.beneficiary_clinic_repository.verify(beneficiary_clinic)

            if check_beneficiary_clinic:
                return Result.bad_request("Relacionamento beneficiário-clínica já cadastrado")

            beneficiary_clinic.created_at = datetime.utcnow()
            beneficiary_clinic.updated_at = datetime.utcnow()

            await self.beneficiary_clinic_repository.add(beneficiary_clinic)

            check_beneficiary_clinic = await self.beneficiary_clinic_repository.verify(beneficiary_clinic)

            if check_beneficiary_clinic:
                return Result.ok(check_beneficiary_clinic)

            return Result.error(f"Erro ao cadastrar relacionamento beneficiário-clínica no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar relacionamento beneficiário-clínica")
