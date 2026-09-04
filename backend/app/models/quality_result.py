from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class QualityResult(Base):
    __tablename__ = "quality_results"

    id = Column(Integer, primary_key=True, index=True)

    inspection_id = Column(
        Integer,
        ForeignKey("inspections.id"),
        nullable=False
    )

    defect_type = Column(
        String(100),
        nullable=True
    )

    confidence_score = Column(
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

    is_passed = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    inspection = relationship(
        "Inspection",
        back_populates="quality_results"
    )