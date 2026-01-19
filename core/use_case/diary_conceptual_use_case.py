from datetime import datetime

import numpy as np
from infrastructure.models.diary_conceptual import DiaryConceptual
from infrastructure.models.diary_embedding_gemini import DiaryEmbeddingGemini
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.diary_embedding_gemini_repository import DiaryEmbeddingGeminiRepository
from infrastructure.services.llm_service import LLMService
from core.kernel.result import Result


class DiaryConceptualUseCase:
    def __init__(
            self,
            llm_service: LLMService,
            beneficiary_repository: BeneficiaryRepository,
            diary_embedding_gemini_repository: DiaryEmbeddingGeminiRepository
            ):

        self.llm_service = llm_service
        self.beneficiary_repository = beneficiary_repository
        self.diary_embedding_gemini_repository = diary_embedding_gemini_repository

    async def execute(self, diary: DiaryConceptual, user_id: str):
        try:
            beneficiary = await self.beneficiary_repository.get_by_id(diary.beneficiary_id)

            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            self.llm_service.configure("gemini")
            provider = self.llm_service.getProvider()

            chunks = self.llm_service.split_text(f'{diary.custom_questions}')

            for chunk in chunks:
                embedding = await self.llm_service.generate_embeddings(chunk)

                if provider == "gemini":
                    if len(embedding) == 768:
                        if isinstance(embedding, list):
                            embedding = np.array(embedding)

                        meta_data = {
                            "type": "diary",
                            "created_by": user_id
                        }
                        if diary.custom_questions:
                            meta_data["custom_questions"] = diary.custom_questions

                        diary_embedding = DiaryEmbeddingGemini(
                            diary_id=None,  # Não há diary_id pois não salvamos na tabela diary
                            beneficiary_id=diary.beneficiary_id,
                            content=chunk,
                            meta_data=meta_data,
                            embedding=embedding,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        await self.diary_embedding_gemini_repository.add(diary_embedding)

            return Result.ok({"value": "Diário cadastrado com sucesso", "beneficiary_id": diary.beneficiary_id})
        except Exception as e:
            return Result.error(f"Erro ao cadastrar diário: {str(e)}")
