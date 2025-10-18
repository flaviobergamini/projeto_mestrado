from core.kernel.result import Result
from infrastructure.repositories.beneficiary_clinic_repository import BeneficiaryClinicRepository

class ListBeneficiaryClinicUseCase:
    def __init__(self, beneficiary_clinic_repository: BeneficiaryClinicRepository):
        self.beneficiary_clinic_repository = beneficiary_clinic_repository

    async def execute(self):
        try:
            beneficiary_clinics = await self.beneficiary_clinic_repository.list_all()
            return Result.ok(beneficiary_clinics)
        except Exception as e:
            return Result.error(f"Erro ao listar relacionamentos beneficiário-clínica")
