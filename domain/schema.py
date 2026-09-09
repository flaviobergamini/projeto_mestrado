from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

from core.constants.demographics import INCOME_BRACKETS


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "professor"
    municipality_id: Optional[str] = None
    school_id: Optional[str] = None
    teacher_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ConfirmEmail(BaseModel):
    email: EmailStr
    code: str


class ResendConfirmation(BaseModel):
    email: EmailStr


class ForgotPassword(BaseModel):
    email: EmailStr


class ConfirmResetPassword(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class RefreshToken(BaseModel):
    email: EmailStr
    refresh_token: str


class UpdateRoleRequest(BaseModel):
    role: str


class UpdateOwnDemographics(BaseModel):
    """Demografia autodeclarada do responsável — preenchida por ele mesmo, com
    consentimento explícito, nunca em nome dele por um admin. Usada apenas nas
    métricas agregadas de nível de adesão do painel administrativo."""
    birth_year: Optional[int] = None
    income_bracket: Optional[str] = None
    single_parent: Optional[bool] = None
    children_count: Optional[int] = None
    neurodivergent_children_count: Optional[int] = None
    consent: bool = False

    @field_validator("income_bracket")
    @classmethod
    def _validate_income_bracket(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in INCOME_BRACKETS:
            raise ValueError(f"income_bracket deve ser um de: {sorted(INCOME_BRACKETS)}")
        return v
