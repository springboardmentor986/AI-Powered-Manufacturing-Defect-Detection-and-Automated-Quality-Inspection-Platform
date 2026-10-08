from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: str = "quality_engineer"
    department: Optional[str] = "Manufacturing Quality Control"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str # Accepts username or email
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
