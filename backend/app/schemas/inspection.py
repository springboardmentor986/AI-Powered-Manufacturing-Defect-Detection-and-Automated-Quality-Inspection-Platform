from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class InspectionRecordBase(BaseModel):
    category: str = "general"
    split: str = "upload"
    defect_type: str = "unclassified"
    notes: Optional[str] = None

class InspectionRecordCreate(InspectionRecordBase):
    batch_id: Optional[str] = None

class InspectionRecordResponse(InspectionRecordBase):
    id: str
    batch_id: Optional[str] = None
    image_filename: str
    image_url: str
    thumbnail_url: Optional[str] = None
    original_filename: str
    file_size_bytes: int
    image_width: int
    image_height: int
    color_channels: int
    file_format: str
    image_hash: Optional[str] = None
    status: str
    quality_decision: str
    confidence_score: Optional[float] = None
    severity_score: Optional[float] = None
    severity_level: Optional[str] = None
    inspection_metadata: Dict[str, Any] = {}
    uploaded_by: Optional[int] = None
    operator_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BatchInspectionCreate(BaseModel):
    batch_name: str
    description: Optional[str] = None
    category: Optional[str] = None

class BatchInspectionResponse(BaseModel):
    id: str
    batch_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    total_images: int
    processed_images: int
    pass_count: int
    fail_count: int
    review_count: int
    status: str
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DashboardKPIStats(BaseModel):
    total_inspections: int
    total_passed: int
    total_failed: int
    total_review: int
    total_pending: int
    pass_rate_percentage: float
    defect_rate_percentage: float
    total_batches: int
    active_batches: int = 0
    high_severity_alerts: int = 0
    average_inference_latency_ms: float = 0.0
    executive_compliance_percentage: float = 100.0
    total_dataset_samples: int = 5354
    station_sync_percentage: float = 100.0
    categories_covered: int
    system_status: str
    category_distribution: Dict[str, int]
    recent_inspections: List[InspectionRecordResponse]
