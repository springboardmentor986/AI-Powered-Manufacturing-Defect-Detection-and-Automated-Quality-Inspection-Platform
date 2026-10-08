import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.audit import SystemAuditLog
from ..models.user import User

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("visioninspect")

def log_audit_event(
    db: Session,
    action: str,
    user: Optional[User] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """Save an audit event to the database and logger"""
    try:
        audit_entry = SystemAuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            status=status,
            details=details or {},
            ip_address=ip_address
        )
        db.add(audit_entry)
        db.commit()
        logger.info(f"AUDIT: [{action}] by user={user.username if user else 'ANONYMOUS'} - Status: {status}")
    except Exception as e:
        logger.error(f"Failed to record audit log: {str(e)}")
        db.rollback()
