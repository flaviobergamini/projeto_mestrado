from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from core.services.jwt_service import JwtService
from core.use_case.create_beneficiary_use_case import CreateBeneficiaryUseCase
from core.use_case.create_health_plan_use_case import CreateHealthPlanUseCase
from core.use_case.create_school_use_case import CreateSchoolUseCase
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from core.use_case.list_health_plan_use_case import ListHealthPlanUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.query_diary_use_case import QueryDiaryUseCase
from infrastructure.database_context.database import Database
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.diary_embedding_groq_repository import DiaryEmbeddingGroqRepository
from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
from infrastructure.repositories.health_plan_repository import HealthPlanRepository
from infrastructure.repositories.school_repository import SchoolRepository
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.services.deepseek_service import DeepseekService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.gpt_service import GptService
from infrastructure.services.llm_service import LLMService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["api.diary_routes", "api.auth_routes", "api.beneficiary_routes", "api.health_plan_routes", "api.school_routes"],
    )

    config = providers.Configuration()

    database = providers.Singleton(Database, url=config.database.url)

    # Services
    gpt_service = providers.Factory(GptService)
    gemini_service = providers.Factory(GeminiService)
    deepseek_service = providers.Factory(DeepseekService)
    llm_service = providers.Factory(LLMService)

    jwt_service = providers.Factory(JwtService)

    # Repositories
    diary_embedding_repository=providers.Factory(
        DiaryEmbeddingRepository, database=database
    )

    diary_embedding_groq_repository=providers.Factory(
        DiaryEmbeddingGroqRepository, database=database
    )

    user_repository=providers.Factory(
        UserRepository, database=database
    ) 

    beneficiary_repository = providers.Factory(
        BeneficiaryRepository, database=database
    )

    school_repository = providers.Factory(
        SchoolRepository, database=database
    )

    health_plan_repository = providers.Factory(
        HealthPlanRepository, database=database
    )

    # Use cases
    diary_embedding_use_case=providers.Factory(
        DiaryEmbeddingUseCase,
        diary_embedding_repository=diary_embedding_repository,
        llm_service=llm_service,
        diary_embedding_groq_repository=diary_embedding_groq_repository,
        beneficiary_repository=beneficiary_repository
    )

    query_diary_use_case=providers.Factory(
        QueryDiaryUseCase,
        diary_embedding_repository=diary_embedding_repository,
        llm_service=llm_service,
        diary_embedding_groq_repository=diary_embedding_groq_repository
    )

    create_user_use_case=providers.Factory(
        CreateUserUseCase,
        user_repository=user_repository,
        jwt_service=jwt_service
    ) 

    login_user_use_case=providers.Factory(
        LoginUserUseCase,
        user_repository=user_repository,
        jwt_service=jwt_service
    ) 

    create_beneficiary_use_case=providers.Factory(
        CreateBeneficiaryUseCase,
        beneficiary_repository=beneficiary_repository
    )

    create_school_use_case=providers.Factory(
        CreateSchoolUseCase,
        school_repository=school_repository
    )

    create_health_plan_use_case=providers.Factory(
        CreateHealthPlanUseCase,
        health_plan_repository=health_plan_repository
    )

    list_health_plan_use_case=providers.Factory(
        ListHealthPlanUseCase,
        health_plan_repository=health_plan_repository
    )



