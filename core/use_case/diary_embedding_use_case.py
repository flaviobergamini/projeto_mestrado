from datetime import datetime
from infrastructure.models.diary_embedding import DiaryEmbedding
from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
from infrastructure.services.gpt_service import GptService
import numpy as np

class DiaryEmbeddingUseCase:
    def __init__(self, diary_embedding_repository: DiaryEmbeddingRepository, gpt_service: GptService):
        self.diary_embedding_repository=diary_embedding_repository
        self.gpt_service=gpt_service

    async def execute(self, diary: str):
        try:
            prompt = f"""
            Resuma o seguinte diário em um parágrafo único curto e claro, mantendo o sentido principal e abordando todos os ocorridos:

            Diário:
            {diary}
            """

            summary = await self.gpt_service.chat(prompt)

            embedding = await self.gpt_service.generate_embeddings(summary)

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
        except Exception as e:
            print(f"Erro no DiaryEmbeddingUseCase: {e}")
            raise