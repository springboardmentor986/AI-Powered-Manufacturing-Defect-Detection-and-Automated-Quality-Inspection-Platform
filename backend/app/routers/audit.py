from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.audit import SystemAuditLog
from ..models.user import User, UserRole
from ..utils.dependencies import require_roles

router = APIRouter(prefix="/audit", tags=["Security & System Audit Trails"])

@router.get("/logs")
def get_audit_logs(
    action: Optional[str] = None,
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_roles([UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Retrieve system audit logs (Restricted to Supervisors & Managers)"""
    query = db.query(SystemAuditLog)
    if action:
        query = query.filter(SystemAuditLog.action == action)
    
    logs = query.order_by(SystemAuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user_email": l.user_email,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "status": l.status,
            "ip_address": l.ip_address,
            "details": l.details,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None
        }
        for l in logs
    ]
