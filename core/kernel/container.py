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
from infrastructure.repositories.case_study_draft_repository import CaseStudyDraftRepository
from infrastructure.repositories.parent_student_link_repository import ParentStudentLinkRepository
from infrastructure.repositories.therapist_student_link_repository import TherapistStudentLinkRepository
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.generated_pei_repository import GeneratedPeiRepository
from infrastructure.repositories.municipality_repository import MunicipalityRepository
from infrastructure.repositories.audit_repository import AuditRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.repositories.links_repository import LinksRepository
from infrastructure.repositories.diary_summary_repository import DiarySummaryRepository
from infrastructure.repositories.metrics_repository import MetricsRepository
from infrastructure.repositories.skill_repository import SkillRepository
from infrastructure.repositories.diary_question_repository import DiaryQuestionRepository
from infrastructure.repositories.bncc_repository import BnccRepository
from infrastructure.repositories.skill_plan_repository import SkillPlanRepository
from infrastructure.services.ai_gateway import AiGateway
from core.use_case.kanban import kanban_use_cases as kb_uc
from core.use_case.functional_profile import functional_profile_use_cases as fp_uc
from infrastructure.services.report_pdf_generator import ReportPdfGenerator
from core.use_case.bncc import bncc_use_cases as bncc_uc
from core.use_case.links.links_use_cases import (
    ListStudentsWithLinksUseCase, ListLinkableTeachersUseCase, SetStudentTeachersUseCase,
    SetTeacherStudentsUseCase, GetRelationsUseCase,
)
from core.use_case.skill_plan.generate_skill_plan_draft_use_case import GenerateSkillPlanDraftUseCase
from core.use_case.skill_plan.suggest_skill_scores_use_case import SuggestSkillScoresUseCase
from core.use_case.skill_plan.list_skill_suggestions_use_case import ListSkillSuggestionsUseCase
from core.use_case.skill_plan.decide_skill_suggestion_use_case import DecideSkillSuggestionUseCase
from infrastructure.repositories.functional_profile_repository import FunctionalProfileRepository
from infrastructure.repositories.pei_kanban_repository import PeiKanbanRepository
from infrastructure.repositories.saved_skill_result_repository import SavedSkillResultRepository
from infrastructure.services.anonymization_service import AnonymizationService
from infrastructure.services.cognito_service import CognitoService
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.bncc_context import BnccContext
from infrastructure.services.rag_service import RagService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "api.auth_routes", "api.dependencies",
            "api.student_routes", "api.diary_routes", "api.pdi_routes",
            "api.school_routes", "api.teacher_routes", "api.case_study_routes",
            "api.chat_routes", "api.prompt_routes", "api.pei_gen_routes",
            "api.municipality_routes", "api.admin_routes", "api.ai_usage_routes",
            "api.links_routes", "api.family_routes", "api.diary_summary_routes",
            "api.metrics_routes", "api.skill_routes", "api.pei_kanban_routes", "api.saved_skill_routes",
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

    case_study_draft_repository = providers.Factory(CaseStudyDraftRepository, database=database)

    parent_student_link_repository = providers.Factory(ParentStudentLinkRepository, database=database)

    therapist_student_link_repository = providers.Factory(TherapistStudentLinkRepository, database=database)

    chat_repository = providers.Factory(ChatRepository, database=database)

    prompt_repository = providers.Factory(PromptRepository, database=database)

    generated_pei_repository = providers.Factory(GeneratedPeiRepository, database=database)

    municipality_repository = providers.Factory(MunicipalityRepository, database=database)

    audit_repository = providers.Factory(AuditRepository, database=database)

    ai_usage_repository = providers.Factory(AiUsageRepository, database=database)

    # Singleton: guarda o nome/validade do cache explícito do catálogo BNCC entre requisições.
    bncc_context = providers.Singleton(BnccContext, database=database, gemini=gemini_service, usage_repo=ai_usage_repository)

    links_repository = providers.Factory(LinksRepository, database=database)

    diary_summary_repository = providers.Factory(DiarySummaryRepository, database=database)

    metrics_repository = providers.Factory(MetricsRepository, database=database)

    skill_repository = providers.Factory(SkillRepository, database=database)

    diary_question_repository = providers.Factory(DiaryQuestionRepository, database=database)

    bncc_repository = providers.Factory(BnccRepository, database=database)

    skill_plan_repository = providers.Factory(SkillPlanRepository, database=database)

    functional_profile_repository = providers.Factory(FunctionalProfileRepository, database=database)

    pei_kanban_repository = providers.Factory(PeiKanbanRepository, database=database)

    saved_skill_result_repository = providers.Factory(SavedSkillResultRepository, database=database)

    anonymization_service = providers.Factory(AnonymizationService, database=database)

    list_students_with_links_use_case = providers.Factory(ListStudentsWithLinksUseCase, repository=links_repository)
    list_linkable_teachers_use_case = providers.Factory(ListLinkableTeachersUseCase, teachers=teacher_repository)
    set_student_teachers_use_case = providers.Factory(SetStudentTeachersUseCase, repository=links_repository)
    set_teacher_students_use_case = providers.Factory(SetTeacherStudentsUseCase, repository=links_repository)
    get_relations_use_case = providers.Factory(GetRelationsUseCase, repository=links_repository)

    report_pdf_generator = providers.Factory(ReportPdfGenerator)
    list_kanban_cards_use_case = providers.Factory(kb_uc.ListKanbanCardsUseCase, repository=pei_kanban_repository)
    create_kanban_card_use_case = providers.Factory(kb_uc.CreateKanbanCardUseCase, repository=pei_kanban_repository)
    update_kanban_card_use_case = providers.Factory(kb_uc.UpdateKanbanCardUseCase, repository=pei_kanban_repository)
    delete_kanban_card_use_case = providers.Factory(kb_uc.DeleteKanbanCardUseCase, repository=pei_kanban_repository)
    create_cards_from_skill_use_case = providers.Factory(kb_uc.CreateCardsFromSkillUseCase, repository=pei_kanban_repository)
    bncc_list_grades_use_case = providers.Factory(bncc_uc.ListGradesUseCase, repository=bncc_repository)
    bncc_list_areas_use_case = providers.Factory(bncc_uc.ListAreasUseCase, repository=bncc_repository)
    bncc_list_skills_use_case = providers.Factory(bncc_uc.ListSkillsUseCase, repository=bncc_repository)
    bncc_create_skill_use_case = providers.Factory(bncc_uc.CreateSkillUseCase, repository=bncc_repository)
    bncc_update_skill_use_case = providers.Factory(bncc_uc.UpdateSkillUseCase, repository=bncc_repository)
    bncc_delete_skill_use_case = providers.Factory(bncc_uc.DeleteSkillUseCase, repository=bncc_repository)
    bncc_list_student_skills_use_case = providers.Factory(bncc_uc.ListStudentSkillsUseCase, repository=bncc_repository)
    bncc_set_skill_score_use_case = providers.Factory(bncc_uc.SetSkillScoreUseCase, repository=bncc_repository)
    bncc_list_skill_events_use_case = providers.Factory(bncc_uc.ListSkillEventsUseCase, repository=bncc_repository)
    bncc_create_report_use_case = providers.Factory(bncc_uc.CreateSkillReportUseCase, repository=bncc_repository)
    bncc_list_reports_use_case = providers.Factory(bncc_uc.ListSkillReportsUseCase, repository=bncc_repository)
    bncc_get_report_use_case = providers.Factory(bncc_uc.GetSkillReportUseCase, repository=bncc_repository)
    bncc_delete_report_use_case = providers.Factory(bncc_uc.DeleteSkillReportUseCase, repository=bncc_repository)
    bncc_report_pdf_use_case = providers.Factory(
        bncc_uc.RenderSkillReportPdfUseCase, repository=bncc_repository, students=student_repository,
        pdf=report_pdf_generator,
    )

    ai_gateway = providers.Factory(
        AiGateway, gemini=gemini_service, usage_repo=ai_usage_repository, anonymization=anonymization_service,
        bncc_context=bncc_context,
    )

    list_functional_domains_use_case = providers.Factory(fp_uc.ListFunctionalDomainsUseCase)
    generate_functional_profile_use_case = providers.Factory(
        fp_uc.GenerateFunctionalProfileUseCase, repository=functional_profile_repository,
        students=student_repository, bncc=bncc_repository, ai=ai_gateway,
    )
    create_manual_profile_use_case = providers.Factory(fp_uc.CreateManualProfileUseCase, repository=functional_profile_repository)
    list_student_profiles_use_case = providers.Factory(fp_uc.ListStudentProfilesUseCase, repository=functional_profile_repository)
    get_profile_evolution_use_case = providers.Factory(fp_uc.GetProfileEvolutionUseCase, repository=functional_profile_repository)
    get_profile_use_case = providers.Factory(fp_uc.GetProfileUseCase, repository=functional_profile_repository)
    update_profile_use_case = providers.Factory(fp_uc.UpdateProfileUseCase, repository=functional_profile_repository)
    delete_profile_use_case = providers.Factory(fp_uc.DeleteProfileUseCase, repository=functional_profile_repository)

    generate_skill_plan_draft_use_case = providers.Factory(
        GenerateSkillPlanDraftUseCase, repository=skill_plan_repository, students=student_repository, ai=ai_gateway,
    )
    suggest_skill_scores_use_case = providers.Factory(
        SuggestSkillScoresUseCase, repository=skill_plan_repository, students=student_repository, ai=ai_gateway,
    )
    list_skill_suggestions_use_case = providers.Factory(ListSkillSuggestionsUseCase, repository=skill_plan_repository)
    decide_skill_suggestion_use_case = providers.Factory(DecideSkillSuggestionUseCase, repository=skill_plan_repository)

    rag_service = providers.Factory(RagService, database=database, gemini=gemini_service, usage_repo=ai_usage_repository, diary_repo=diary_repository)

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
