from pydantic import BaseModel, EmailStr
from datetime import date


class DiaryRequest(BaseModel):
    diary: str
    model: str
    beneficiary_id: int

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