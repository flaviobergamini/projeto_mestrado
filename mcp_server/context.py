"""
Lazy singleton factories para todos os repositórios e serviços usados pelo MCP server.
Cada getter cria a instância uma única vez e reutiliza nas chamadas subsequentes.
"""
from infrastructure.database_context.database import Database
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.pdi_repository import PdiRepository
from infrastructure.repositories.case_study_repository import CaseStudyRepository
from infrastructure.repositories.case_study_draft_repository import CaseStudyDraftRepository
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.generated_pei_repository import GeneratedPeiRepository
from infrastructure.repositories.school_repository import SchoolRepository
from infrastructure.repositories.teacher_repository import TeacherRepository
from infrastructure.repositories.vinculos_repository import VinculosRepository
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.repositories.municipality_repository import MunicipalityRepository
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.rag_service import RagService
from infrastructure.services.anonymization_service import AnonymizationService

# ── Singletons ────────────────────────────────────────────────────────────────

_db: Database | None = None
_gemini: GeminiService | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def get_gemini() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini


# ── Repository factories (lightweight — apenas envolvem o db) ─────────────────

def get_student_repo() -> StudentRepository:
    return StudentRepository(get_db())


def get_diary_repo() -> DiaryRepository:
    return DiaryRepository(get_db())


def get_pdi_repo() -> PdiRepository:
    return PdiRepository(get_db())


def get_case_study_repo() -> CaseStudyRepository:
    return CaseStudyRepository(get_db())


def get_case_study_draft_repo() -> CaseStudyDraftRepository:
    return CaseStudyDraftRepository(get_db())


def get_chat_repo() -> ChatRepository:
    return ChatRepository(get_db())


def get_prompt_repo() -> PromptRepository:
    return PromptRepository(get_db())


def get_generated_pei_repo() -> GeneratedPeiRepository:
    return GeneratedPeiRepository(get_db())


def get_school_repo() -> SchoolRepository:
    return SchoolRepository(get_db())


def get_teacher_repo() -> TeacherRepository:
    return TeacherRepository(get_db())


def get_vinculos_repo() -> VinculosRepository:
    return VinculosRepository(get_db())


def get_user_repo() -> UserRepository:
    return UserRepository(get_db())


def get_ai_usage_repo() -> AiUsageRepository:
    return AiUsageRepository(get_db())


def get_municipality_repo() -> MunicipalityRepository:
    return MunicipalityRepository(get_db())


# ── Service factories (dependências encadeadas) ───────────────────────────────

def get_anonymization_service() -> AnonymizationService:
    return AnonymizationService(database=get_db())


def get_rag_service() -> RagService:
    return RagService(
        database=get_db(),
        gemini=get_gemini(),
        usage_repo=get_ai_usage_repo(),
        diary_repo=get_diary_repo(),
    )
