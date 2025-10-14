from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from core.services.jwt_service import JwtService
from core.use_case.create_beneficiary_use_case import CreateBeneficiaryUseCase
from core.use_case.create_health_plan_use_case import CreateHealthPlanUseCase
from core.use_case.create_school_use_case import CreateSchoolUseCase
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.delete_beneficiary_use_case import DeleteBeneficiaryUseCase
from core.use_case.delete_health_plan_use_case import DeleteHealthPlanUseCase
from core.use_case.delete_school_use_case import DeleteSchoolUseCase
from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from core.use_case.get_beneficiary_use_case import GetBeneficiaryByIdUseCase
from core.use_case.get_health_plan_by_id_use_case import GetHealthPlanByIdUseCase
from core.use_case.get_school_by_id_use_case import GetSchoolByIdUseCase
from core.use_case.list_beneficiary_use_case import ListBeneficiaryUseCase
from core.use_case.list_health_plan_use_case import ListHealthPlanUseCase
from core.use_case.list_school_use_case import ListSchoolUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.query_diary_use_case import QueryDiaryUseCase
from core.use_case.update_beneficiary_use_case import UpdateBeneficiaryUseCase
from core.use_case.update_health_plan_use_case import UpdateHealthPlanUseCase
from core.use_case.update_school_use_case import UpdateSchoolUseCase
from core.use_case.create_clinic_use_case import CreateClinicUseCase
from core.use_case.list_clinic_use_case import ListClinicUseCase
from core.use_case.get_clinic_by_id_use_case import GetClinicByIdUseCase
from core.use_case.update_clinic_use_case import UpdateClinicUseCase
from core.use_case.delete_clinic_use_case import DeleteClinicUseCase
from core.use_case.create_professional_use_case import CreateProfessionalUseCase
from core.use_case.list_professional_use_case import ListProfessionalUseCase
from core.use_case.get_professional_by_id_use_case import GetProfessionalByIdUseCase
from core.use_case.update_professional_use_case import UpdateProfessionalUseCase
from core.use_case.delete_professional_use_case import DeleteProfessionalUseCase
from infrastructure.database_context.database import Database
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.clinic_repository import ClinicRepository
from infrastructure.repositories.professional_repository import ProfessionalRepository
from infrastructure.repositories.diary_embedding_gemini_repository import DiaryEmbeddingGeminiRepository
from infrastructure.repositories.diary_embedding_groq_repository import DiaryEmbeddingGroqRepository
from infrastructure.repositories.diary_embedding_repository import DiaryEmbeddingRepository
from infrastructure.repositories.health_plan_repository import HealthPlanRepository
from infrastructure.repositories.school_repository import SchoolRepository
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.services.llm_service import LLMService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["api.diary_routes", "api.auth_routes", "api.beneficiary_routes", "api.health_plan_routes", "api.school_routes", "api.clinic_routes", "api.professional_routes"],
    )

    config = providers.Configuration()

    database = providers.Singleton(Database, url=config.database.url)

    # Services
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

    diary_embedding_gemini_repository = providers.Factory(
        DiaryEmbeddingGeminiRepository, database=database
    )

    clinic_repository = providers.Factory(
        ClinicRepository, database=database
    )

    professional_repository = providers.Factory(
        ProfessionalRepository, database=database
    )

    # Use cases
    diary_embedding_use_case=providers.Factory(
        DiaryEmbeddingUseCase,
        diary_embedding_repository=diary_embedding_repository,
        llm_service=llm_service,
        diary_embedding_groq_repository=diary_embedding_groq_repository,
        beneficiary_repository=beneficiary_repository,
        diary_embedding_gemini_repository=diary_embedding_gemini_repository
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

    list_school_use_case=providers.Factory(
        ListSchoolUseCase,
        school_repository=school_repository
    )

    get_school_by_id_use_case=providers.Factory(
        GetSchoolByIdUseCase,
        school_repository=school_repository
    )

    get_health_plan_by_id_use_case=providers.Factory(
        GetHealthPlanByIdUseCase,
        health_plan_repository=health_plan_repository
    )

    update_school_use_case=providers.Factory(
        UpdateSchoolUseCase,
        school_repository=school_repository
    )

    delete_school_use_case=providers.Factory(
        DeleteSchoolUseCase,
        school_repository=school_repository
    )

    update_health_plan_use_case=providers.Factory(
        UpdateHealthPlanUseCase,
        health_plan_repository=health_plan_repository
    )

    delete_health_plan_use_case=providers.Factory(
        DeleteHealthPlanUseCase,
        health_plan_repository=health_plan_repository
    )

    list_beneficiary_use_case=providers.Factory(
        ListBeneficiaryUseCase,
        beneficiary_repository=beneficiary_repository
    )

    get_beneficiary_use_case=providers.Factory(
        GetBeneficiaryByIdUseCase,
        beneficiary_repository=beneficiary_repository
    )

    update_beneficiary_use_case=providers.Factory(
        UpdateBeneficiaryUseCase,
        beneficiary_repository=beneficiary_repository
    )

    delete_beneficiary_use_case=providers.Factory(
        DeleteBeneficiaryUseCase,
        beneficiary_repository=beneficiary_repository
    )

    # Clinic use cases
    create_clinic_use_case=providers.Factory(
        CreateClinicUseCase,
        clinic_repository=clinic_repository
    )

    list_clinic_use_case=providers.Factory(
        ListClinicUseCase,
        clinic_repository=clinic_repository
    )

    get_clinic_by_id_use_case=providers.Factory(
        GetClinicByIdUseCase,
        clinic_repository=clinic_repository
    )

    update_clinic_use_case=providers.Factory(
        UpdateClinicUseCase,
        clinic_repository=clinic_repository
    )

    delete_clinic_use_case=providers.Factory(
        DeleteClinicUseCase,
        clinic_repository=clinic_repository
    )

    # Professional use cases
    create_professional_use_case=providers.Factory(
        CreateProfessionalUseCase,
        professional_repository=professional_repository
    )

    list_professional_use_case=providers.Factory(
        ListProfessionalUseCase,
        professional_repository=professional_repository
    )

    get_professional_by_id_use_case=providers.Factory(
        GetProfessionalByIdUseCase,
        professional_repository=professional_repository
    )

    update_professional_use_case=providers.Factory(
        UpdateProfessionalUseCase,
        professional_repository=professional_repository
    )

    delete_professional_use_case=providers.Factory(
        DeleteProfessionalUseCase,
        professional_repository=professional_repository
    )