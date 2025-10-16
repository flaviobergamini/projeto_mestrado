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
from core.use_case.create_beneficiary_clinic_use_case import CreateBeneficiaryClinicUseCase
from core.use_case.list_beneficiary_clinic_use_case import ListBeneficiaryClinicUseCase
from core.use_case.get_beneficiary_clinic_by_id_use_case import GetBeneficiaryClinicByIdUseCase
from core.use_case.update_beneficiary_clinic_use_case import UpdateBeneficiaryClinicUseCase
from core.use_case.delete_beneficiary_clinic_use_case import DeleteBeneficiaryClinicUseCase
from core.use_case.create_autismia_use_case import CreateAutismiaUseCase
from core.use_case.list_autismia_use_case import ListAutismiaUseCase
from core.use_case.get_autismia_by_id_use_case import GetAutismiaByIdUseCase
from core.use_case.update_autismia_use_case import UpdateAutismiaUseCase
from core.use_case.delete_autismia_use_case import DeleteAutismiaUseCase
from core.use_case.create_evaluation_use_case import CreateEvaluationUseCase
from core.use_case.list_evaluation_use_case import ListEvaluationUseCase
from core.use_case.get_evaluation_by_id_use_case import GetEvaluationByIdUseCase
from core.use_case.update_evaluation_use_case import UpdateEvaluationUseCase
from core.use_case.delete_evaluation_use_case import DeleteEvaluationUseCase
from core.use_case.create_family_reunion_use_case import CreateFamilyReunionUseCase
from core.use_case.list_family_reunion_use_case import ListFamilyReunionUseCase
from core.use_case.get_family_reunion_by_id_use_case import GetFamilyReunionByIdUseCase
from core.use_case.update_family_reunion_use_case import UpdateFamilyReunionUseCase
from core.use_case.delete_family_reunion_use_case import DeleteFamilyReunionUseCase
from core.use_case.create_school_feedback_use_case import CreateSchoolFeedbackUseCase
from core.use_case.list_school_feedback_use_case import ListSchoolFeedbackUseCase
from core.use_case.get_school_feedback_by_id_use_case import GetSchoolFeedbackByIdUseCase
from core.use_case.update_school_feedback_use_case import UpdateSchoolFeedbackUseCase
from core.use_case.delete_school_feedback_use_case import DeleteSchoolFeedbackUseCase
from core.use_case.create_supervisor_use_case import CreateSupervisorUseCase
from core.use_case.list_supervisor_use_case import ListSupervisorUseCase
from core.use_case.get_supervisor_by_id_use_case import GetSupervisorByIdUseCase
from core.use_case.update_supervisor_use_case import UpdateSupervisorUseCase
from core.use_case.delete_supervisor_use_case import DeleteSupervisorUseCase
from core.use_case.create_therapeutic_plan_use_case import CreateTherapeuticPlanUseCase
from core.use_case.list_therapeutic_plan_use_case import ListTherapeuticPlanUseCase
from core.use_case.get_therapeutic_plan_by_id_use_case import GetTherapeuticPlanByIdUseCase
from core.use_case.update_therapeutic_plan_use_case import UpdateTherapeuticPlanUseCase
from core.use_case.delete_therapeutic_plan_use_case import DeleteTherapeuticPlanUseCase
from core.use_case.create_therapeutic_sessions_use_case import CreateTherapeuticSessionsUseCase
from core.use_case.list_therapeutic_sessions_use_case import ListTherapeuticSessionsUseCase
from core.use_case.get_therapeutic_sessions_by_id_use_case import GetTherapeuticSessionsByIdUseCase
from core.use_case.update_therapeutic_sessions_use_case import UpdateTherapeuticSessionsUseCase
from core.use_case.delete_therapeutic_sessions_use_case import DeleteTherapeuticSessionsUseCase
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
from infrastructure.repositories.beneficiary_clinic_repository import BeneficiaryClinicRepository
from infrastructure.repositories.autismia_repository import AutismiaRepository
from infrastructure.repositories.evaluation_repository import EvaluationRepository
from infrastructure.repositories.family_reunion_repository import FamilyReunionRepository
from infrastructure.repositories.school_feedback_repository import SchoolFeedbackRepository
from infrastructure.repositories.supervisor_repository import SupervisorRepository
from infrastructure.repositories.therapeutic_plan_repository import TherapeuticPlanRepository
from infrastructure.repositories.therapeutic_sessions_repository import TherapeuticSessionsRepository
from infrastructure.services.llm_service import LLMService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["api.diary_routes", "api.auth_routes", "api.beneficiary_routes", "api.health_plan_routes", "api.school_routes", "api.clinic_routes", "api.professional_routes", "api.beneficiary_clinic_routes", "api.autismia_routes", "api.evaluation_routes", "api.family_reunion_routes", "api.school_feedback_routes", "api.supervisor_routes", "api.therapeutic_plan_routes", "api.therapeutic_sessions_routes"],
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

    beneficiary_clinic_repository = providers.Factory(
        BeneficiaryClinicRepository, database=database
    )

    autismia_repository = providers.Factory(
        AutismiaRepository, database=database
    )

    evaluation_repository = providers.Factory(
        EvaluationRepository, database=database
    )

    family_reunion_repository = providers.Factory(
        FamilyReunionRepository, database=database
    )

    school_feedback_repository = providers.Factory(
        SchoolFeedbackRepository, database=database
    )

    supervisor_repository = providers.Factory(
        SupervisorRepository, database=database
    )

    therapeutic_plan_repository = providers.Factory(
        TherapeuticPlanRepository, database=database
    )

    therapeutic_sessions_repository = providers.Factory(
        TherapeuticSessionsRepository, database=database
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

    # Beneficiary Clinic use cases
    create_beneficiary_clinic_use_case=providers.Factory(
        CreateBeneficiaryClinicUseCase,
        beneficiary_clinic_repository=beneficiary_clinic_repository
    )

    list_beneficiary_clinic_use_case=providers.Factory(
        ListBeneficiaryClinicUseCase,
        beneficiary_clinic_repository=beneficiary_clinic_repository
    )

    get_beneficiary_clinic_by_id_use_case=providers.Factory(
        GetBeneficiaryClinicByIdUseCase,
        beneficiary_clinic_repository=beneficiary_clinic_repository
    )

    update_beneficiary_clinic_use_case=providers.Factory(
        UpdateBeneficiaryClinicUseCase,
        beneficiary_clinic_repository=beneficiary_clinic_repository
    )

    delete_beneficiary_clinic_use_case=providers.Factory(
        DeleteBeneficiaryClinicUseCase,
        beneficiary_clinic_repository=beneficiary_clinic_repository
    )

    # Autismia use cases
    create_autismia_use_case=providers.Factory(
        CreateAutismiaUseCase,
        autismia_repository=autismia_repository
    )

    list_autismia_use_case=providers.Factory(
        ListAutismiaUseCase,
        autismia_repository=autismia_repository
    )

    get_autismia_by_id_use_case=providers.Factory(
        GetAutismiaByIdUseCase,
        autismia_repository=autismia_repository
    )

    update_autismia_use_case=providers.Factory(
        UpdateAutismiaUseCase,
        autismia_repository=autismia_repository
    )

    delete_autismia_use_case=providers.Factory(
        DeleteAutismiaUseCase,
        autismia_repository=autismia_repository
    )

    # Evaluation use cases
    create_evaluation_use_case=providers.Factory(
        CreateEvaluationUseCase,
        evaluation_repository=evaluation_repository
    )

    list_evaluation_use_case=providers.Factory(
        ListEvaluationUseCase,
        evaluation_repository=evaluation_repository
    )

    get_evaluation_by_id_use_case=providers.Factory(
        GetEvaluationByIdUseCase,
        evaluation_repository=evaluation_repository
    )

    update_evaluation_use_case=providers.Factory(
        UpdateEvaluationUseCase,
        evaluation_repository=evaluation_repository
    )

    delete_evaluation_use_case=providers.Factory(
        DeleteEvaluationUseCase,
        evaluation_repository=evaluation_repository
    )

    # Family Reunion use cases
    create_family_reunion_use_case=providers.Factory(
        CreateFamilyReunionUseCase,
        family_reunion_repository=family_reunion_repository
    )

    list_family_reunion_use_case=providers.Factory(
        ListFamilyReunionUseCase,
        family_reunion_repository=family_reunion_repository
    )

    get_family_reunion_by_id_use_case=providers.Factory(
        GetFamilyReunionByIdUseCase,
        family_reunion_repository=family_reunion_repository
    )

    update_family_reunion_use_case=providers.Factory(
        UpdateFamilyReunionUseCase,
        family_reunion_repository=family_reunion_repository
    )

    delete_family_reunion_use_case=providers.Factory(
        DeleteFamilyReunionUseCase,
        family_reunion_repository=family_reunion_repository
    )

    # School Feedback use cases
    create_school_feedback_use_case=providers.Factory(
        CreateSchoolFeedbackUseCase,
        school_feedback_repository=school_feedback_repository
    )

    list_school_feedback_use_case=providers.Factory(
        ListSchoolFeedbackUseCase,
        school_feedback_repository=school_feedback_repository
    )

    get_school_feedback_by_id_use_case=providers.Factory(
        GetSchoolFeedbackByIdUseCase,
        school_feedback_repository=school_feedback_repository
    )

    update_school_feedback_use_case=providers.Factory(
        UpdateSchoolFeedbackUseCase,
        school_feedback_repository=school_feedback_repository
    )

    delete_school_feedback_use_case=providers.Factory(
        DeleteSchoolFeedbackUseCase,
        school_feedback_repository=school_feedback_repository
    )

    # Supervisor use cases
    create_supervisor_use_case=providers.Factory(
        CreateSupervisorUseCase,
        supervisor_repository=supervisor_repository
    )

    list_supervisor_use_case=providers.Factory(
        ListSupervisorUseCase,
        supervisor_repository=supervisor_repository
    )

    get_supervisor_by_id_use_case=providers.Factory(
        GetSupervisorByIdUseCase,
        supervisor_repository=supervisor_repository
    )

    update_supervisor_use_case=providers.Factory(
        UpdateSupervisorUseCase,
        supervisor_repository=supervisor_repository
    )

    delete_supervisor_use_case=providers.Factory(
        DeleteSupervisorUseCase,
        supervisor_repository=supervisor_repository
    )

    # Therapeutic Plan use cases
    create_therapeutic_plan_use_case=providers.Factory(
        CreateTherapeuticPlanUseCase,
        therapeutic_plan_repository=therapeutic_plan_repository
    )

    list_therapeutic_plan_use_case=providers.Factory(
        ListTherapeuticPlanUseCase,
        therapeutic_plan_repository=therapeutic_plan_repository
    )

    get_therapeutic_plan_by_id_use_case=providers.Factory(
        GetTherapeuticPlanByIdUseCase,
        therapeutic_plan_repository=therapeutic_plan_repository
    )

    update_therapeutic_plan_use_case=providers.Factory(
        UpdateTherapeuticPlanUseCase,
        therapeutic_plan_repository=therapeutic_plan_repository
    )

    delete_therapeutic_plan_use_case=providers.Factory(
        DeleteTherapeuticPlanUseCase,
        therapeutic_plan_repository=therapeutic_plan_repository
    )

    # Therapeutic Sessions use cases
    create_therapeutic_sessions_use_case=providers.Factory(
        CreateTherapeuticSessionsUseCase,
        therapeutic_sessions_repository=therapeutic_sessions_repository
    )

    list_therapeutic_sessions_use_case=providers.Factory(
        ListTherapeuticSessionsUseCase,
        therapeutic_sessions_repository=therapeutic_sessions_repository
    )

    get_therapeutic_sessions_by_id_use_case=providers.Factory(
        GetTherapeuticSessionsByIdUseCase,
        therapeutic_sessions_repository=therapeutic_sessions_repository
    )

    update_therapeutic_sessions_use_case=providers.Factory(
        UpdateTherapeuticSessionsUseCase,
        therapeutic_sessions_repository=therapeutic_sessions_repository
    )

    delete_therapeutic_sessions_use_case=providers.Factory(
        DeleteTherapeuticSessionsUseCase,
        therapeutic_sessions_repository=therapeutic_sessions_repository
    )