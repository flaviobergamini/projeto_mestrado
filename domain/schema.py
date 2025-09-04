from pydantic import BaseModel, EmailStr
from typing import List


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