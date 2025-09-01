from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from core.use_case.query_diary_use_case import QueryDiaryUseCase
from infrastructure.database_context.database import Database
from infrastructure.repositories.diary_embedding_groq_repository import DiaryEmbeddingGroqRepository
from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
from infrastructure.services.deepseek_service import DeepseekService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.gpt_service import GptService
from infrastructure.services.llm_service import LLMService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["api.routes"],
    )

    config = providers.Configuration()

    database = providers.Singleton(Database, url=config.database.url)

    # Services
    gpt_service = providers.Factory(GptService)
    gemini_service = providers.Factory(GeminiService)
    deepseek_service = providers.Factory(DeepseekService)
    llm_service = providers.Factory(LLMService)

    # Repositories
    diary_embedding_repository=providers.Factory(
        DiaryEmbeddingRepository, database=database
    )

    diary_embedding_groq_repository=providers.Factory(
        DiaryEmbeddingGroqRepository, database=database
    )

    # Use cases
    diary_embedding_use_case=providers.Factory(
        DiaryEmbeddingUseCase,
        diary_embedding_repository=diary_embedding_repository,
        llm_service=llm_service,
        diary_embedding_groq_repository=diary_embedding_groq_repository
    )

    query_diary_use_case=providers.Factory(
        QueryDiaryUseCase,
        diary_embedding_repository=diary_embedding_repository,
        llm_service=llm_service,
        diary_embedding_groq_repository=diary_embedding_groq_repository
    )







