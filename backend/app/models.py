from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(20), default="inspector")  # admin / inspector
    created_at = Column(TIMESTAMP, server_default=func.now())


class Category(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), unique=True, nullable=False)
    category_type = Column(String(30))   # object / texture
    dataset_name = Column(String(100))   # MVTec AD
    created_at = Column(TIMESTAMP, server_default=func.now())


class Image(Base):
    __tablename__ = "images"
    image_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    uploaded_by = Column(Integer, ForeignKey("users.user_id"))
    image_path = Column(String, nullable=False)
    image_source = Column(String(30))   # mvtec / uploaded
    image_type = Column(String(30))     # train / test / uploaded
    created_at = Column(TIMESTAMP, server_default=func.now())


class Inspection(Base):
    __tablename__ = "inspections"
    inspection_id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.image_id"))
    inspected_by = Column(Integer, ForeignKey("users.user_id"))
    status = Column(String(30), default="pending")     # pending / completed / failed
    result = Column(String(30))                          # normal / defective
    confidence_score = Column(DECIMAL(5, 2))
    inspection_time = Column(TIMESTAMP, server_default=func.now())


class Defect(Base):
    __tablename__ = "defects"
    defect_id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.inspection_id"))
    defect_type = Column(String(100))    # scratch / crack / hole
    severity = Column(String(20))        # low / medium / high
    location_data = Column(JSON)         # bounding box coords
    created_at = Column(TIMESTAMP, server_default=func.now())


class InspectionResult(Base):
    __tablename__ = "inspection_results"
    result_id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.inspection_id"))
    model_name = Column(String(100))
    model_version = Column(String(50))
    prediction = Column(String(50))
    confidence_score = Column(DECIMAL(5, 2))
    processing_time_ms = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
