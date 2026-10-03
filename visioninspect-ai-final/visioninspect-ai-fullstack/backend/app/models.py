"""
Milestone 1 - Database schema: users, inspection_images, defect_records.
Four roles: admin, quality_engineer, factory_supervisor, production_manager.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(24), unique=True, index=True, nullable=False)
    full_name = Column(String(80), nullable=False)
    role = Column(String(32), nullable=False, default="quality_engineer")
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class InspectionImage(Base):
    __tablename__ = "inspection_images"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    product_line = Column(String(80), nullable=True)
    batch_id = Column(String(80), nullable=True)
    width = Column(Integer)
    height = Column(Integer)
    status = Column(String(16), default="review")   # pass | fail | review
    annotated_path = Column(String(255), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    defects = relationship("DefectRecord", back_populates="image", cascade="all, delete-orphan")

class DefectRecord(Base):
    __tablename__ = "defect_records"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("inspection_images.id"))
    defect_type = Column(String(32))          # crack | scratch | dent | contamination
    bbox_x = Column(Integer); bbox_y = Column(Integer)
    bbox_w = Column(Integer); bbox_h = Column(Integer)
    area_px = Column(Integer)
    size_score = Column(Float)
    location_score = Column(Float)
    type_score = Column(Float)
    confidence_score = Column(Float)
    severity_score = Column(Float)
    severity_level = Column(String(16))        # critical | high | medium | low
    extra = Column(JSON, nullable=True)         # solidity/extent/aspect etc, for debugging

    image = relationship("InspectionImage", back_populates="defects")
