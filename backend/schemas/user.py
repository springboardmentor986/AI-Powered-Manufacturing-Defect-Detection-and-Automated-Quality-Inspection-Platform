from pydantic import BaseModel, EmailStr
from enum import Enum


class UserRole(str, Enum):
    QUALITY_ENGINEER = "quality_engineer"
    FACTORY_SUPERVISOR = "factory_supervisor"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str