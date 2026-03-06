from core.kernel.result import Result
from infrastructure.repositories.user_beneficiary_repository import UserBeneficiaryRepository


class ListBeneficiariesByUserUseCase:
    def __init__(self, user_beneficiary_repository: UserBeneficiaryRepository):
        self.user_beneficiary_repository = user_beneficiary_repository

    async def execute(self, user_id: int):
        try:
            beneficiaries = await self.user_beneficiary_repository.list_by_user(user_id)
            return Result.ok(beneficiaries)
        except Exception as e:
            return Result.err("Erro ao listar beneficiários do usuário")
