from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Boolean,
)

from sqlalchemy.sql import func

from database import Base




class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="quality_engineer"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )




class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )



    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    
    image_path = Column(
        String(500),
        nullable=False
    )

    
    product_category = Column(
        String(100),
        nullable=False
    )

    
    prediction = Column(
        String(50),
        nullable=False
    )

    

    anomaly_score = Column(
        String(50),
        nullable=False
    )

    threshold = Column(
        String(50),
        nullable=False
    )



    defect_type = Column(
        String(100),
        nullable=True
    )

    classification_confidence = Column(
        Float,
        nullable=True
    )

    

    severity_score = Column(
        Float,
        nullable=True
    )

    severity_level = Column(
        String(50),
        nullable=True
    )

    recommended_action = Column(
        String(50),
        nullable=True
    )

   
  

    manual_review = Column(
        Boolean,
        nullable=True,
        default=False
    )

    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )