from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.diary import Diary
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository


class CreateDiaryUseCase:
    """
    Caso de uso para criar um novo registro diário.
    Valida se o beneficiário existe e se já não há um registro para a mesma data.
    Opcionalmente, pode disparar geração de embeddings de forma assíncrona.
    """

    def __init__(
        self,
        diary_repository: DiaryRepository,
        beneficiary_repository: BeneficiaryRepository,
        generate_embedding_use_case=None,  # Injeção opcional
    ):
        self.diary_repository = diary_repository
        self.beneficiary_repository = beneficiary_repository
        self.generate_embedding_use_case = generate_embedding_use_case

    async def execute(self, diary: Diary):
        try:
            # Verificar se o beneficiário existe
            beneficiary = await self.beneficiary_repository.get_by_id(diary.beneficiary_id)
            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            # Verificar se já existe um registro para essa data
            check_diary = await self.diary_repository.verify(diary)
            if check_diary:
                return Result.bad_request(
                    "Já existe um registro diário para este beneficiário nesta data"
                )

            # Configurar timestamps
            diary.created_at = datetime.utcnow()
            diary.updated_at = datetime.utcnow()

            # Adicionar ao banco de dados
            await self.diary_repository.add(diary)

            # Verificar se foi criado com sucesso
            check_diary = await self.diary_repository.verify(diary)
            if check_diary:
                # Tentar gerar embeddings (não bloqueia se falhar)
                if self.generate_embedding_use_case:
                    try:
                        await self.generate_embedding_use_case.execute(check_diary.id)
                    except Exception as e:
                        # Log do erro mas não falha a criação do diário
                        print(f"Aviso: Erro ao gerar embeddings: {str(e)}")

                return Result.ok(check_diary)

            return Result.error("Erro ao cadastrar registro diário no sistema")
        except Exception as e:
            return Result.error(f"Erro ao cadastrar registro diário: {str(e)}")
