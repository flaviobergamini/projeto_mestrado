from pydantic import BaseModel, EmailStr
from typing import Optional


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
