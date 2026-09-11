from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    QUALITY_ENGINEER = "quality_engineer"
    SUPERVISOR = "supervisor"

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.QUALITY_ENGINEER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ProductCreate(BaseModel):
    product_name: str
    product_code: str

class ProductResponse(BaseModel):
    id: int
    product_name: str
    product_code: str
    created_at: datetime

    class Config:
        from_attributes = True

class InspectionCreate(BaseModel):
    product_id: int

class InspectionResponse(BaseModel):
    id: int
    product_id: int
    image_path: str
    processed_image_path: Optional[str] = None
    image_filename: str
    status: str
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    file_size: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True