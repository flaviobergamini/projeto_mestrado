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