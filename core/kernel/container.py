from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from core.use_case.query_diary_use_case import QueryDiaryUseCase
from infrastructure.database_context.database import Database
from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
from infrastructure.services.deepseek_service import DeepseekService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.gpt_service import GptService


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

    # Repositories
    diary_embedding_repository=providers.Factory(
        DiaryEmbeddingRepository, database=database
    )

    # Use cases
    diary_embedding_use_case=providers.Factory(
        DiaryEmbeddingUseCase,
        diary_embedding_repository=diary_embedding_repository,
        gpt_service=gpt_service
    )

    query_diary_use_case=providers.Factory(
        QueryDiaryUseCase,
        diary_embedding_repository=diary_embedding_repository,
        gpt_service=gpt_service
    )







