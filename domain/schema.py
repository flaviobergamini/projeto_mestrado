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

    # Mídia (fotos e vídeos)
    photos: Optional[dict] = None  # Lista de URLs/paths de fotos
    videos: Optional[dict] = None  # Lista de URLs/paths de vídeos


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

    # Mídia (fotos e vídeos)
    photos: Optional[dict] = None  # Lista de URLs/paths de fotos
    videos: Optional[dict] = None  # Lista de URLs/paths de vídeos


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

    # Mídia (fotos e vídeos)
    photos: Optional[dict] = None  # Lista de URLs/paths de fotos
    videos: Optional[dict] = None  # Lista de URLs/paths de vídeos

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

class VerifyEmail(BaseModel):
    token: str

class RefreshToken(BaseModel):
    refresh_token: str

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

class StudyCaseRequest(BaseModel):
    beneficiary_id: int
    custom_questions: Optional[dict] = None

    '''# Informações gerais do aluno
    student_difficulties: str | None
    student_likes_school: bool | None
    observation_question_above: str | None
    student_has_friends: bool | None
    which_friends: str | None
    student_has_favorite_classmate: bool | None
    which_favorite_classmate: str | None
    students_favorite_activities: str | None
    students_difficult_tasks_and_reasons: str | None
    students_express_needs_in_what_way: str | None
    student_asks_teachers_for_help_why: str | None
    # Novas perguntas — seção de percepções e apoios
    student_opinion_about_teachers: str | None
    student_opinion_about_school_importance: str | None
    student_school_supports: str | None
    student_satisfied_with_supports: str | None
    student_wants_other_supports: str | None
    student_special_interest: str | None
    student_participation_in_activities: str | None
    student_easy_and_difficult_activities: str | None
    student_participation_level: str | None
    student_specific_needs_and_barriers: str | None
    student_clinical_or_educational_services: str | None
    teachers_opinion_about_student_expectations: str | None
    teachers_evaluation_about_student_performance: str | None
    teachers_concerns_and_suggested_supports: str | None
    school_community_perception_about_interaction: str | None
    teachers_expectations_about_student: str | None
    student_skills_and_potential: str | None
    reason_for_requesting_aee_services: str | None
    school_accessibility_resources: str | None
    school_resources_evaluation: str | None
    student_affective_and_social_involvement: str | None
    school_opinion_about_student_development: str | None
    # Família
    family_opinion_about_school_life: str | None
    family_involvement_with_school: str | None
    family_awareness_of_inclusive_rights: str | None
    family_identified_skills_and_difficulties: str | None
    family_expectations_about_development: str | None
    # Aspectos socioemocionais e comportamentais
    interacts_without_constant_mediation: bool | None
    initiates_social_interactions_spontaneously: bool | None
    participates_with_stimuli: bool | None
    waits_turn_and_handles_frustration: bool | None
    shares_experiences_or_limited_interactions: bool | None
    expresses_basic_emotions_clearly: bool | None
    reacts_positively_to_praise: bool | None
    seeks_emotional_support: bool | None
    emotionally_dysregulated_with_routine_changes: bool | None
    calms_down_with_minimal_help: bool | None
    interested_in_learning_new_things: bool | None
    follows_simple_instructions: bool | None
    maintains_attention_appropriately: bool | None
    solves_simple_problems_independently: bool | None
    learns_better_with_visual_support: bool | None
    # Aspectos motores e de autocuidado
    fine_motor_coordination: bool | None
    gross_motor_coordination: bool | None
    performs_self_care_independently: bool | None
    participates_in_physical_activities_without_fatigue: bool | None
    shows_repetitive_motor_behaviors: bool | None
    # Alimentação
    limited_food_repertoire: str | None
    needs_physical_assistance_to_eat: str | None
    discomfort_with_food_touching: str | None
    eats_better_in_quiet_environment: str | None
    challenging_behavior_during_meals: str | None
    # Comunicação escola-família
    frequent_school_family_communication: bool | None
    family_provides_emotional_support: bool | None
    family_collaboration_in_therapeutic_resources: bool | None
    family_open_to_new_approaches: bool | None
    family_participates_in_events: bool | None
    # Contatos e informações adicionais
    family_email: str | None
    pedagogical_adaptations: str | None
    pedagogical_development: str | None
    additional_personal_information: str | None
    # Identificação
    mother_name: str | None
    father_name: str | None
    school_name: str | None
    main_teacher_name: str | None
    assistant_teacher_name: str | None'''

class GeneratePEIRequest(BaseModel):
    beneficiary_id: int

class GeneratePEIResponse(BaseModel):
    pei_id: int
    beneficiary_id: int
    generated_at: str
    message: str

class GeneratePEIPDFRequest(BaseModel):
    pei_id: int

class GeneratePEIPDFResponse(BaseModel):
    pdf_path: str
    pdf_url: str
    pei_id: int
    beneficiary_id: int
    generated_at: str

class InstitutionStudyCaseRequest(BaseModel):
    beneficiary_id: int
    custom_questions: Optional[dict] = None
    '''institution_name: str
    institution_cnpj: str | None
    institution_type: str | None
    operating_hours: str | None
    full_address: str | None
    contact_phone: str | None
    institutional_email: str | None
    website: str | None
    education_levels_offered: str | None
    total_students: str | None
    total_students_with_tea: str | None
    max_capacity_students_with_tea: str | None
    total_classrooms: str | None
    has_multifunctional_resource_rooms: str | None
    has_sensory_or_relaxation_rooms: str | None
    physical_accessibility_adaptations: str | None
    total_teachers: str | None
    teachers_with_special_education_training: str | None
    teachers_with_tea_training: str | None
    has_multidisciplinary_team: str | None
    tea_training_frequency: str | None
    tea_training_methodologies: str | None
    mediators_or_support_teachers_count: str | None
    student_mediator_ratio: str | None
    curriculum_adaptation_practices: str | None
    teaching_methods_for_tea_students: str | None
    individualized_education_plan_creation: str | None
    evaluation_process_for_tea_students: str | None
    alternative_communication_resources: str | None
    visual_resources_for_routine_and_organization: str | None
    neurotypical_and_tea_students_integration: str | None
    sensory_stimulus_control: str | None
    adapted_materials_available: str | None
    has_spaces_for_crisis_or_sensory_overload: str | None
    provides_recess_or_break_adaptations: str | None
    technological_resources_for_tea_support: str | None
    provides_weighted_materials_for_sensory_regulation: str | None
    daily_communication_with_families: str | None
    meetings_with_parents_frequency: str | None
    provides_home_continuity_guidance: str | None
    has_support_group_for_families: str | None
    promotes_family_inclusive_events: str | None
    allows_external_therapists: str | None
    partnerships_with_specialized_clinics: str | None
    pedagogical_and_therapeutic_integration: str | None
    participates_in_inclusion_support_networks: str | None
    medication_administration_protocol: str | None
    has_certification_for_tea_service: str | None
    required_documents_for_enrollment: str | None
    issues_periodic_development_reports: str | None
    has_public_agency_agreements: str | None
    student_progress_tracking_method: str | None'''


class DiaryConceptualRequest(BaseModel):
    """Schema para criação de registro diário conceitual (texto único)"""
    beneficiary_id: int
    custom_questions: Optional[dict] = None