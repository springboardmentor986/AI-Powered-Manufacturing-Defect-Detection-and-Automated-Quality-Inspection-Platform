import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from ..database import Base

class SystemAuditLog(Base):
    __tablename__ = "system_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True) # USER_LOGIN, IMAGE_UPLOAD, BATCH_CREATED, INSPECTION_VIEWED, ROLE_SWITCH
    resource_type = Column(String(50), nullable=True) # inspection, batch, user, dataset
    resource_id = Column(String(100), nullable=True)
    status = Column(String(20), default="SUCCESS") # SUCCESS, FAILURE, WARNING
    ip_address = Column(String(50), nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
