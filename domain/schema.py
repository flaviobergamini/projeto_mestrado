from pydantic import BaseModel, EmailStr
from typing import List


class RAGRequest(BaseModel):
    pergunta: str
    model: str

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