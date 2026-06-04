from dependency_injector import containers, providers

from core.services.jwt_service import JwtService
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.refresh_token_use_case import RefreshTokenUseCase
from infrastructure.database_context.database import Database
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.services.gemini_service import GeminiService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["api.auth_routes"],
    )

    config = providers.Configuration()

    database = providers.Singleton(Database, url=config.database.url)

    jwt_service = providers.Factory(JwtService)

    gemini_service = providers.Factory(GeminiService)

    user_repository = providers.Factory(UserRepository, database=database)

    create_user_use_case = providers.Factory(
        CreateUserUseCase,
        user_repository=user_repository,
        jwt_service=jwt_service,
    )

    login_user_use_case = providers.Factory(
        LoginUserUseCase,
        user_repository=user_repository,
        jwt_service=jwt_service,
    )

    refresh_token_use_case = providers.Factory(
        RefreshTokenUseCase,
        user_repository=user_repository,
        jwt_service=jwt_service,
    )
