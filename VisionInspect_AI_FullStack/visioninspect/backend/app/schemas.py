import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole, SeverityLevel, InspectionStatus


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.quality_engineer


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: dt.datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Defect records ----------

class DefectRecordOut(BaseModel):
    id: int
    defect_type: str
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    area_px: int
    size_score: float
    location_score: float
    type_score: float
    confidence_score: float
    severity_score: float
    severity_level: SeverityLevel

    class Config:
        from_attributes = True


# ---------- Inspection images ----------

class InspectionImageOut(BaseModel):
    id: int
    filename: str
    product_line: Optional[str]
    batch_id: Optional[str]
    uploaded_at: dt.datetime
    width: Optional[int]
    height: Optional[int]
    status: InspectionStatus
    processed: bool
    defects: List[DefectRecordOut] = []

    class Config:
        from_attributes = True


class InspectionImageSummary(BaseModel):
    id: int
    filename: str
    status: InspectionStatus
    uploaded_at: dt.datetime
    defect_count: int
    max_severity: Optional[SeverityLevel]

    class Config:
        from_attributes = True


# ---------- Analytics ----------

class DefectTrendPoint(BaseModel):
    date: str
    total_inspections: int
    total_defects: int
    fail_count: int
    pass_count: int


class DefectTypeBreakdown(BaseModel):
    defect_type: str
    count: int


class SeverityBreakdown(BaseModel):
    severity_level: str
    count: int


class AnalyticsSummary(BaseModel):
    total_images: int
    total_defects: int
    pass_count: int
    fail_count: int
    review_count: int
    pass_rate: float
    defect_type_breakdown: List[DefectTypeBreakdown]
    severity_breakdown: List[SeverityBreakdown]
    trend: List[DefectTrendPoint]
