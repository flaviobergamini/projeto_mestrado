from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional


class DiaryEmbeddingRequest(BaseModel):
    """Schema antigo para geração de embeddings"""
    diary: str
    model: str
    beneficiary_id: int


class DiaryQueryRAGRequest(BaseModel):
    """Schema para consultas RAG sobre diários"""
    beneficiary_id: int
    query: str
    limit: Optional[int] = 10


class BehaviorAnalysisRequest(BaseModel):
    """Schema para análise de padrões comportamentais"""
    beneficiary_id: int
    days: Optional[int] = 30
    analysis_type: Optional[str] = "comprehensive"  # comprehensive, crisis, progress


class GenerateEmbeddingRequest(BaseModel):
    """Schema para gerar embeddings de um diário específico"""
    diary_id: int


class DiaryCreateRequest(BaseModel):
    """Schema para criação de registro diário completo"""
    beneficiary_id: int
    diary_date: date

    # Comportamento
    behavior_description: Optional[str] = None
    behavior_rating: Optional[int] = None  # 1-5

    # Atividades
    activity_performance: Optional[str] = None
    activity_engagement: Optional[int] = None  # 1-5
    completed_activities: Optional[str] = None

    # Socialização
    socialization_description: Optional[str] = None
    peer_interaction: Optional[int] = None  # 1-5
    adult_interaction: Optional[int] = None  # 1-5

    # Crise
    crisis_occurred: bool = False
    crisis_description: Optional[str] = None
    crisis_trigger: Optional[str] = None
    crisis_intervention: Optional[str] = None
    crisis_duration_minutes: Optional[int] = None

    # Estado emocional
    emotional_state: Optional[str] = None
    mood_rating: Optional[int] = None  # 1-5

    # Comunicação
    communication_description: Optional[str] = None
    verbal_communication: Optional[int] = None  # 1-5
    non_verbal_communication: Optional[int] = None  # 1-5

    # Autonomia
    autonomy_description: Optional[str] = None
    self_care_skills: Optional[int] = None  # 1-5
    task_independence: Optional[int] = None  # 1-5

    # Observações
    general_observations: Optional[str] = None
    teacher_suggestions: Optional[str] = None
    adaptations_needed: Optional[str] = None
    achievements: Optional[str] = None


class DiaryUpdateRequest(BaseModel):
    """Schema para atualização de registro diário"""
    diary_date: Optional[date] = None

    # Comportamento
    behavior_description: Optional[str] = None
    behavior_rating: Optional[int] = None

    # Atividades
    activity_performance: Optional[str] = None
    activity_engagement: Optional[int] = None
    completed_activities: Optional[str] = None

    # Socialização
    socialization_description: Optional[str] = None
    peer_interaction: Optional[int] = None
    adult_interaction: Optional[int] = None

    # Crise
    crisis_occurred: Optional[bool] = None
    crisis_description: Optional[str] = None
    crisis_trigger: Optional[str] = None
    crisis_intervention: Optional[str] = None
    crisis_duration_minutes: Optional[int] = None

    # Estado emocional
    emotional_state: Optional[str] = None
    mood_rating: Optional[int] = None

    # Comunicação
    communication_description: Optional[str] = None
    verbal_communication: Optional[int] = None
    non_verbal_communication: Optional[int] = None

    # Autonomia
    autonomy_description: Optional[str] = None
    self_care_skills: Optional[int] = None
    task_independence: Optional[int] = None

    # Observações
    general_observations: Optional[str] = None
    teacher_suggestions: Optional[str] = None
    adaptations_needed: Optional[str] = None
    achievements: Optional[str] = None


class DiaryResponse(BaseModel):
    """Schema de resposta com dados do diário"""
    id: int
    beneficiary_id: int
    user_id: int
    diary_date: str

    # Comportamento
    behavior_description: Optional[str] = None
    behavior_rating: Optional[int] = None

    # Atividades
    activity_performance: Optional[str] = None
    activity_engagement: Optional[int] = None
    completed_activities: Optional[str] = None

    # Socialização
    socialization_description: Optional[str] = None
    peer_interaction: Optional[int] = None
    adult_interaction: Optional[int] = None

    # Crise
    crisis_occurred: bool
    crisis_description: Optional[str] = None
    crisis_trigger: Optional[str] = None
    crisis_intervention: Optional[str] = None
    crisis_duration_minutes: Optional[int] = None

    # Estado emocional
    emotional_state: Optional[str] = None
    mood_rating: Optional[int] = None

    # Comunicação
    communication_description: Optional[str] = None
    verbal_communication: Optional[int] = None
    non_verbal_communication: Optional[int] = None

    # Autonomia
    autonomy_description: Optional[str] = None
    self_care_skills: Optional[int] = None
    task_independence: Optional[int] = None

    # Observações
    general_observations: Optional[str] = None
    teacher_suggestions: Optional[str] = None
    adaptations_needed: Optional[str] = None
    achievements: Optional[str] = None

    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    name:str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str

class SchoolRequest(BaseModel):
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class SchoolResponse(BaseModel):
    id: int
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class HealthPlanRequest(BaseModel):
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class HealthPlanResponse(BaseModel):
    id: int
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class BeneficiaryRequest(BaseModel):
    name: str
    date_of_birth: date 
    diagnosis: str
    main_responsible: str
    responsible_contact: str
    entry_date: date
    exit_date: date
    status: str
    school_id: int
    healthplan_id: int

class BeneficiaryResponse(BaseModel):
    id: int
    name: str
    date_of_birth: str
    diagnosis: str
    main_responsible: str
    responsible_contact: str
    entry_date: str
    exit_date: str
    status: str
    school_id: int
    healthplan_id: int

class ClinicRequest(BaseModel):
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class ClinicResponse(BaseModel):
    id: int
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class ProfessionalRequest(BaseModel):
    name: str
    function: str
    specialty: str
    contact: str
    availability: str
    clinic_id: int
    email: str
    password: str

class ProfessionalResponse(BaseModel):
    id: int
    name: str
    function: str
    specialty: str
    contact: str
    availability: str
    clinic_id: int
    email: str

class BeneficiaryClinicRequest(BaseModel):
    beneficiary_id: int
    clinic_id: int
    start_date: date
    end_date: date

class BeneficiaryClinicResponse(BaseModel):
    id: int
    beneficiary_id: int
    clinic_id: int
    start_date: str
    end_date: str

class AutismiaRequest(BaseModel):
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class AutismiaResponse(BaseModel):
    id: int
    name: str
    address: str
    telephone: str
    email: str
    responsible: str

class EvaluationRequest(BaseModel):
    beneficiary_id: int
    date: date
    type: str
    evaluation_result: str
    details: str

class EvaluationResponse(BaseModel):
    id: int
    beneficiary_id: int
    date: str
    type: str
    evaluation_result: str
    details: str

class FamilyReunionRequest(BaseModel):
    beneficiary_id: int
    supervisor_id: int
    reunion_date: date
    description: str
    family_feedback: str

class FamilyReunionResponse(BaseModel):
    id: int
    beneficiary_id: int
    supervisor_id: int
    reunion_date: str
    description: str
    family_feedback: str

class SchoolFeedbackRequest(BaseModel):
    beneficiary_id: int
    supervisor_id: int
    feedback_date: date
    observation: str
    tracking_status: str

class SchoolFeedbackResponse(BaseModel):
    id: int
    beneficiary_id: int
    supervisor_id: int
    feedback_date: str
    observation: str
    tracking_status: str

class SupervisorRequest(BaseModel):
    name: str
    specialty: str
    contact: str
    availability: str
    autismia_id: int
    email: str
    password: str

class SupervisorResponse(BaseModel):
    id: int
    name: str
    specialty: str
    contact: str
    availability: str
    autismia_id: int
    email: str

class TherapeuticPlanRequest(BaseModel):
    beneficiary_id: int
    start_date: date
    end_date: date
    objective: str
    description: str
    workload: int
    status: str

class TherapeuticPlanResponse(BaseModel):
    id: int
    beneficiary_id: int
    start_date: str
    end_date: str
    objective: str
    description: str
    workload: int
    status: str

class TherapeuticSessionsRequest(BaseModel):
    therapeutic_plan_id: int
    professional_id: int
    clinic_id: int
    session_date: date
    description: str
    observation: str

class TherapeuticSessionsResponse(BaseModel):
    id: int
    therapeutic_plan_id: int
    professional_id: int
    clinic_id: int
    session_date: str
    description: str
    observation: str

class FileUploadResponse(BaseModel):
    """Schema para resposta de upload de arquivo"""
    file_path: str
    public_url: str
    filename: str
    uploaded_at: str
    user_id: str

class FileDeleteRequest(BaseModel):
    """Schema para requisição de remoção de arquivo"""
    file_path: str