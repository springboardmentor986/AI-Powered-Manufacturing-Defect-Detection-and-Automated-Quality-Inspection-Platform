"""
Milestone 1 - Pydantic request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ---- auth ----
class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=6)
    role: str = "quality_engineer"

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    class Config: from_attributes = True

class RoleUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

# ---- defects / inspections ----
class DefectOut(BaseModel):
    id: int
    defect_type: str
    bbox_x: int; bbox_y: int; bbox_w: int; bbox_h: int
    area_px: int
    size_score: float
    location_score: float
    type_score: float
    confidence_score: float
    severity_score: float
    severity_level: str
    class Config: from_attributes = True

class FixSuggestion(BaseModel):
    defect_type: str
    severity_level: str
    likely_cause: str
    suggested_fix: str
    required_action: str

class InspectionOut(BaseModel):
    id: int
    filename: str
    product_line: Optional[str]
    batch_id: Optional[str]
    width: int
    height: int
    status: str
    uploaded_at: datetime
    defects: List[DefectOut] = []
    class Config: from_attributes = True

class AnalyticsSummary(BaseModel):
    total_inspections: int
    pass_count: int
    fail_count: int
    review_count: int
    defect_type_counts: dict
    severity_counts: dict
    inspections_over_time: dict

class ValidationResult(BaseModel):
    n_images: int
    precision: float
    recall: float
    f1: float
    mAP: float
    per_class_ap: dict
    confusion_matrix: dict
    caveat: str = "Computed on synthetic, generated test images with known ground truth. This proves the detection/scoring logic is internally consistent; it is not a guarantee of accuracy on real factory photos."
