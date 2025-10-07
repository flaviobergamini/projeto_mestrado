from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.diary_embedding import DiaryEmbedding
from infrastructure.models.diary_embedding_gemini import DiaryEmbeddingGemini
from infrastructure.models.diary_embedding_groq import DiaryEmbeddingGroq
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.diary_embedding_gemini_repository import DiaryEmbeddingGeminiRepository
from infrastructure.repositories.diary_embedding_groq_repository import DiaryEmbeddingGroqRepository
from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
import numpy as np

from infrastructure.services.llm_service import LLMService

class DiaryEmbeddingUseCase:
    def __init__(
            self, 
            diary_embedding_repository: DiaryEmbeddingRepository, 
            llm_service: LLMService, 
            diary_embedding_groq_repository: DiaryEmbeddingGroqRepository,
            diary_embedding_gemini_repository: DiaryEmbeddingGeminiRepository,
            beneficiary_repository: BeneficiaryRepository
            ):
        self.diary_embedding_repository=diary_embedding_repository
        self.llm_service=llm_service
        self.diary_embedding_groq_repository=diary_embedding_groq_repository
        self.beneficiary_repository=beneficiary_repository
        self.diary_embedding_gemini_repository=diary_embedding_gemini_repository

    async def execute(self, diary: str, model: str, beneficiary_id: int, user_id: str):
        try:
            beneficiary = await self.beneficiary_repository.get_by_id(beneficiary_id)

            #if not beneficiary:
            #    return Result.not_found("Beneficiário não encontrado")
            
            self.llm_service.configure(model)
            provider = self.llm_service.getProvider()

            prompt = f"""
            Resuma o seguinte diário em um parágrafo único curto e claro, mantendo o sentido principal e abordando todos os ocorridos:

            Diário:
            {diary}
            """

            summary = await self.llm_service.chat(prompt)

            if provider == 'groq':
                summary = summary.split("</think>")[-1].strip()

            chunks = self.llm_service.split_text(summary)

            for chunk in chunks:
                embedding = await self.llm_service.generate_embeddings(chunk)

                if provider == "openai":
                    if len(embedding) == 1536:
                        if isinstance(embedding, list):
                            embedding = np.array(embedding)

                    diary_embedding = DiaryEmbedding(
                        content=summary,
                        meta_data={"teste":"teste"},
                        embedding=embedding,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ) 
                
                    await self.diary_embedding_repository.add(diary_embedding)

                if provider == "groq":
                    if len(embedding) == 384:
                        if isinstance(embedding, list):
                            embedding = np.array(embedding)

                    diary_embedding_groq = DiaryEmbeddingGroq(
                        content=summary,
                    meta_data={"teste":"teste"},
                    embedding=embedding,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                    )

                    await self.diary_embedding_groq_repository.add(diary_embedding_groq)

                if provider == "gemini":
                    if len(embedding) == 768:
                        if isinstance(embedding, list):
                            embedding = np.array(embedding)

                    diary_embedding = DiaryEmbeddingGemini(
                        content=summary,
                        meta_data={"teste":"teste"},
                        embedding=embedding,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    await self.diary_embedding_gemini_repository.add(diary_embedding)
            
            return Result.ok({"value": "Diario criado com sucesso"})
        except Exception as e:
            return Result.error("Erro ao criar diario")