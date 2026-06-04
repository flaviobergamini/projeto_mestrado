from pydantic import BaseModel
from typing import Optional


class UserRegister(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "professor"
    municipality_id: Optional[str] = None
    school_id: Optional[str] = None
    teacher_id: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    municipality_id: Optional[str]
    school_id: Optional[str]
    teacher_id: Optional[str]


class UpdateRoleRequest(BaseModel):
    role: str


class RefreshToken(BaseModel):
    refresh_token: str
