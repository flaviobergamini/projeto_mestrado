from datetime import datetime

import numpy as np
from infrastructure.models.institution import Institution
from infrastructure.models.institution_embedding_gemini import InstitutionEmbeddingGemini
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.institution_embedding_gemini_repository import InstitutionEmbeddingGeminiRepository
from infrastructure.services.llm_service import LLMService
from core.kernel.result import Result

class InstitutionUseCase:
    def __init__(
            self,
            llm_service: LLMService,
            beneficiary_repository: BeneficiaryRepository,
            institution_embedding_gemini_repository: InstitutionEmbeddingGeminiRepository
            ):

        self.llm_service=llm_service
        self.beneficiary_repository=beneficiary_repository
        self.institution_embedding_gemini_repository=institution_embedding_gemini_repository

    async def execute(self, institution: Institution, user_id: str):
        try:
            beneficiary = await self.beneficiary_repository.get_by_id(institution.beneficiary_id)

            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            self.llm_service.configure("gemini")
            provider = self.llm_service.getProvider()

            chunks = self.llm_service.split_text(institution.get_info_to_string())

            for chunk in chunks:
                embedding = await self.llm_service.generate_embeddings(chunk)

                if provider == "gemini":
                    if len(embedding) == 768:
                        if isinstance(embedding, list):
                            embedding = np.array(embedding)

                        institution_embedding = InstitutionEmbeddingGemini(
                            beneficiary_id=institution.beneficiary_id,
                            content=chunk,
                            meta_data={"type": "institution", "created_by": user_id},
                            embedding=embedding,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        await self.institution_embedding_gemini_repository.add(institution_embedding)

            return Result.ok({"value": "Instituição cadastrada com sucesso", "beneficiary_id": institution.beneficiary_id})
        except Exception as e:
            return Result.error(f"Erro ao cadastrar instituição: {str(e)}")
