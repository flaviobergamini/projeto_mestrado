from datetime import datetime

import numpy as np
from infrastructure.models.study_case import StudyCase
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.services.llm_service import LLMService
from core.kernel.result import Result

class StudyCaseUseCase:
    def __init__(
            self, 
            llm_service: LLMService, 
            beneficiary_repository: BeneficiaryRepository
            ):

        self.llm_service=llm_service
        self.beneficiary_repository=beneficiary_repository

    async def execute(self, study_case: StudyCase, user_id: str):
        try:
            beneficiary = await self.beneficiary_repository.get_by_id(study_case.beneficiary_id)

            #if not beneficiary:
            #    return Result.not_found("Beneficiário não encontrado")
            
            self.llm_service.configure("gemini")
            provider = self.llm_service.getProvider()

            chunks = self.llm_service.split_text(study_case.get_info_to_string())

            for chunk in chunks:
                embedding = await self.llm_service.generate_embeddings(chunk)

                if provider == "gemini":
                    if len(embedding) == 768:
                        if isinstance(embedding, list):
                            embedding = np.array(embedding)

                    # diary_embedding = DiaryEmbeddingGemini(
                    #     content=summary,
                    #     meta_data={"teste":"teste"},
                    #     embedding=embedding,
                    #     created_at=datetime.utcnow(),
                    #     updated_at=datetime.utcnow()
                    # )
                    # await self.diary_embedding_gemini_repository.add(diary_embedding)
            
            return Result.ok({"value": "Diario criado com sucesso"})
        except Exception as e:
            return Result.error("Erro ao criar diario")    


