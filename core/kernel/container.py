from dependency_injector import containers, providers

from core.services.jwt_service import JwtService
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.refresh_token_use_case import RefreshTokenUseCase
from core.use_case.confirm_email_use_case import ConfirmEmailUseCase
from core.use_case.resend_confirmation_use_case import ResendConfirmationUseCase
from core.use_case.forgot_password_use_case import ForgotPasswordUseCase
from core.use_case.confirm_reset_password_use_case import ConfirmResetPasswordUseCase
from core.use_case.validate_token_use_case import ValidateTokenUseCase
from core.use_case.list_users_use_case import ListUsersUseCase
from core.use_case.update_user_role_use_case import UpdateUserRoleUseCase
from infrastructure.database_context.database import Database
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.pdi_repository import PdiRepository as PdiRepo
from infrastructure.repositories.school_repository import SchoolRepository
from infrastructure.repositories.teacher_repository import TeacherRepository
from infrastructure.repositories.case_study_repository import CaseStudyRepository
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.generated_pei_repository import GeneratedPeiRepository
from infrastructure.repositories.municipality_repository import MunicipalityRepository
from infrastructure.repositories.audit_repository import AuditRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.cognito_service import CognitoService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.rag_service import RagService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "api.auth_routes", "api.dependencies",
            "api.student_routes", "api.diary_routes", "api.pdi_routes",
            "api.school_routes", "api.teacher_routes", "api.case_study_routes",
            "api.chat_routes", "api.prompt_routes", "api.pei_gen_routes",
            "api.municipality_routes", "api.admin_routes", "api.ai_usage_routes",
        ],
    )


    config = providers.Configuration()

    database = providers.Singleton(Database, url=config.database.url)

    jwt_service = providers.Factory(JwtService)

    cognito_service = providers.Factory(CognitoService)

    gemini_service = providers.Factory(GeminiService)

    user_repository = providers.Factory(UserRepository, database=database)

    student_repository = providers.Factory(StudentRepository, database=database)

    diary_repository = providers.Factory(DiaryRepository, database=database)

    pdi_repository = providers.Factory(PdiRepo, database=database)

    school_repository = providers.Factory(SchoolRepository, database=database)

    teacher_repository = providers.Factory(TeacherRepository, database=database)

    case_study_repository = providers.Factory(CaseStudyRepository, database=database)

    chat_repository = providers.Factory(ChatRepository, database=database)

    prompt_repository = providers.Factory(PromptRepository, database=database)

    generated_pei_repository = providers.Factory(GeneratedPeiRepository, database=database)

    municipality_repository = providers.Factory(MunicipalityRepository, database=database)

    audit_repository = providers.Factory(AuditRepository, database=database)

    ai_usage_repository = providers.Factory(AiUsageRepository, database=database)

    rag_service = providers.Factory(RagService, database=database, gemini=gemini_service, usage_repo=ai_usage_repository)

    create_user_use_case = providers.Factory(
        CreateUserUseCase,
        user_repository=user_repository,
        auth_service=cognito_service,
    )

    login_user_use_case = providers.Factory(
        LoginUserUseCase,
        user_repository=user_repository,
        auth_service=cognito_service,
    )

    refresh_token_use_case = providers.Factory(
        RefreshTokenUseCase,
        user_repository=user_repository,
        auth_service=cognito_service,
    )

    confirm_email_use_case = providers.Factory(
        ConfirmEmailUseCase,
        auth_service=cognito_service,
    )

    resend_confirmation_use_case = providers.Factory(
        ResendConfirmationUseCase,
        auth_service=cognito_service,
    )

    forgot_password_use_case = providers.Factory(
        ForgotPasswordUseCase,
        auth_service=cognito_service,
    )

    confirm_reset_password_use_case = providers.Factory(
        ConfirmResetPasswordUseCase,
        auth_service=cognito_service,
    )

    validate_token_use_case = providers.Factory(
        ValidateTokenUseCase,
        auth_service=cognito_service,
        user_repository=user_repository,
    )

    list_users_use_case = providers.Factory(
        ListUsersUseCase,
        user_repository=user_repository,
    )

    update_user_role_use_case = providers.Factory(
        UpdateUserRoleUseCase,
        user_repository=user_repository,
    )
