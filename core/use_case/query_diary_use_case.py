from infrastructure.repositories.diary_embedding_groq_repository import DiaryEmbeddingGroqRepository
from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
from infrastructure.services.llm_service import LLMService


class QueryDiaryUseCase:
    def __init__(
            self, 
            diary_embedding_repository: DiaryEmbeddingRepository, 
            llm_service: LLMService, 
            diary_embedding_groq_repository: DiaryEmbeddingGroqRepository
            ):
        self.diary_embedding_repository=diary_embedding_repository
        self.llm_service=llm_service
        self.diary_embedding_groq_repository=diary_embedding_groq_repository

    async def execute(self, query: str, model: str) -> str:
        try:
            self.llm_service.configure(model)
            provider = self.llm_service.getProvider()

            query_vector = await self.llm_service.generate_embeddings(query)

            if provider == 'openai':
                similar_entries = await self.diary_embedding_repository.search_similar_embeddings(query_vector)

                context = "\n".join([entry.content for entry in similar_entries])

            if provider == 'groq':
                similar_entries = await self.diary_embedding_groq_repository.search_similar_embeddings(query_vector)

                context = "\n".join([entry.content for entry in similar_entries])

            final_prompt = f"Baseado nos registros do diário abaixo, responda de forma consisa: \n\n{context}\n\n Pergunta: {query}"

            return await self.llm_service.chat(final_prompt)
        except Exception as e:
            print(f"Erro no DiaryEmbeddingUseCase: {e}")
            raise