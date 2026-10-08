import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from ..database import Base

class InspectionStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INSPECTED = "INSPECTED"
    FAILED = "FAILED"

class QualityDecision:
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    PENDING = "PENDING"

class BatchInspection(Base):
    __tablename__ = "batch_inspections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    category = Column(String(50), nullable=True)
    total_images = Column(Integer, default=0)
    processed_images = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    status = Column(String(50), default="CREATED") # CREATED, PROCESSING, COMPLETED, FAILED
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = relationship("User", back_populates="batches")
    records = relationship("InspectionRecord", back_populates="batch", cascade="all, delete-orphan")

class InspectionRecord(Base):
    __tablename__ = "inspection_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("batch_inspections.id"), nullable=True)
    
    # Image Metadata
    image_filename = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    image_width = Column(Integer, default=0)
    image_height = Column(Integer, default=0)
    color_channels = Column(Integer, default=3)
    file_format = Column(String(20), default="PNG")
    image_hash = Column(String(64), nullable=True, index=True) # SHA-256

    # Quality & Dataset attributes
    category = Column(String(50), default="general", index=True) # MVTec AD category or custom
    split = Column(String(50), default="upload") # train, test, upload, live_stream
    defect_type = Column(String(100), default="unclassified") # good, crack, scratch, broken_large, etc.
    
    # Inspection state & Decision
    status = Column(String(50), default=InspectionStatus.PENDING, index=True)
    quality_decision = Column(String(50), default=QualityDecision.PENDING, index=True)
    confidence_score = Column(Float, nullable=True)
    severity_score = Column(Float, nullable=True) # 0 - 100
    severity_level = Column(String(50), nullable=True) # Low, Medium, High, Critical
    
    # Extra inspection metadata & metrics
    inspection_metadata = Column(JSON, default=dict)
    notes = Column(Text, nullable=True)
    
    # Operator / Audit
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    batch = relationship("BatchInspection", back_populates="records")
    operator = relationship("User", back_populates="inspections")
