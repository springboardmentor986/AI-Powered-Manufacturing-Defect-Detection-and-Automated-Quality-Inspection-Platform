from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "inspector"

class CategoryCreate(BaseModel):
    category_name: str
    category_type: Optional[str] = "object"
    dataset_name: Optional[str] = None


class CategoryOut(BaseModel):
    category_id: int
    category_name: str
    category_type: Optional[str]
    dataset_name: Optional[str]

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
