from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
from infrastructure.services.gpt_service import GptService


class QueryDiaryUseCase:
    def __init__(self, diary_embedding_repository: DiaryEmbeddingRepository, gpt_service: GptService):
        self.diary_embedding_repository=diary_embedding_repository
        self.gpt_service=gpt_service
    
    async def execute(self, query: str) -> str:
        try:
            query_vector = await self.gpt_service.generate_embeddings(query)
            similar_entries = await self.diary_embedding_repository.search_similar_embeddings(query_vector)

            context = "\n".join([entry.content for entry in similar_entries])
            final_prompt = f"Baseado nos registros do diário abaixo, responda de forma consisa: \n\n{context}\n\n Pergunta: {query}"

            return await self.gpt_service.chat(final_prompt)
        except Exception as e:
            print(f"Erro no DiaryEmbeddingUseCase: {e}")
            raise