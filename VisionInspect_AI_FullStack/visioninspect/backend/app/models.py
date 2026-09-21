import enum
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    quality_engineer = "quality_engineer"
    factory_supervisor = "factory_supervisor"
    production_manager = "production_manager"


class SeverityLevel(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class InspectionStatus(str, enum.Enum):
    pending = "pending"
    pass_ = "pass"
    fail = "fail"
    review = "review"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.quality_engineer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    images = relationship("InspectionImage", back_populates="uploaded_by")


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    annotated_path = Column(String(500), nullable=True)
    product_line = Column(String(120), nullable=True)
    batch_id = Column(String(120), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=dt.datetime.utcnow)

    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    status = Column(Enum(InspectionStatus), default=InspectionStatus.pending)
    processed = Column(Boolean, default=False)

    uploaded_by = relationship("User", back_populates="images")
    defects = relationship("DefectRecord", back_populates="image", cascade="all, delete-orphan")


class DefectRecord(Base):
    __tablename__ = "defect_records"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("inspection_images.id"), nullable=False)

    defect_type = Column(String(80), nullable=False)   # scratch / crack / dent / contamination / unknown
    bbox_x = Column(Integer, nullable=False)
    bbox_y = Column(Integer, nullable=False)
    bbox_w = Column(Integer, nullable=False)
    bbox_h = Column(Integer, nullable=False)
    area_px = Column(Integer, nullable=False)

    size_score = Column(Float, nullable=False)
    location_score = Column(Float, nullable=False)
    type_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    severity_score = Column(Float, nullable=False)
    severity_level = Column(Enum(SeverityLevel), nullable=False)

    created_at = Column(DateTime, default=dt.datetime.utcnow)

    image = relationship("InspectionImage", back_populates="defects")
