from fastapi import APIRouter, Depends
from sqlalchemy import Float, cast, func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.image import Image
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    total_inspections = (
        db.query(func.count(Image.id))
        .filter(Image.severity_score.isnot(None))
        .scalar() or 0
    )
    accepted = (
        db.query(func.count(Image.id))
        .filter(Image.quality_decision == "Accept")
        .scalar() or 0
    )
    rejected = (
        db.query(func.count(Image.id))
        .filter(Image.quality_decision == "Reject")
        .scalar() or 0
    )
    pending_review = (
        db.query(func.count(Image.id))
        .filter(
            Image.severity_score.isnot(None),
            Image.supervisor_decision.is_(None),
        )
        .scalar() or 0
    )
    reviewed = (
        db.query(func.count(Image.id))
        .filter(Image.supervisor_decision.isnot(None))
        .scalar() or 0
    )

    critical = (
        db.query(func.count(Image.id))
        .filter(Image.severity_level == "Critical")
        .scalar() or 0
    )
    high = (
        db.query(func.count(Image.id))
        .filter(Image.severity_level == "High")
        .scalar() or 0
    )
    medium = (
        db.query(func.count(Image.id))
        .filter(Image.severity_level == "Medium")
        .scalar() or 0
    )
    low = (
        db.query(func.count(Image.id))
        .filter(Image.severity_level == "Low")
        .scalar() or 0
    )

    avg_confidence = db.query(func.avg(cast(Image.confidence_score, Float))).filter(
        Image.confidence_score.isnot(None)
    ).scalar()

    avg_severity = db.query(func.avg(cast(Image.severity_score, Float))).filter(
        Image.severity_score.isnot(None)
    ).scalar()

    category_rows = (
        db.query(Image.category, func.count(Image.id).label("count"))
        .filter(Image.category.isnot(None))
        .group_by(Image.category)
        .order_by(func.count(Image.id).desc())
        .all()
    )
    categories = [{"category": cat, "count": count} for cat, count in category_rows]

    defect_rows = (
        db.query(Image.defect_type, func.count(Image.id).label("count"))
        .filter(Image.defect_type.isnot(None))
        .group_by(Image.defect_type)
        .order_by(func.count(Image.id).desc())
        .all()
    )
    defect_types = [{"defect_type": dt, "count": count} for dt, count in defect_rows]

    supervisor_approved = (
        db.query(func.count(Image.id))
        .filter(Image.supervisor_decision == "approved")
        .scalar() or 0
    )
    supervisor_rejected = (
        db.query(func.count(Image.id))
        .filter(Image.supervisor_decision == "rejected")
        .scalar() or 0
    )

    return {
        "total_inspections": total_inspections,
        "accepted": accepted,
        "rejected": rejected,
        "pending_review": pending_review,
        "reviewed": reviewed,
        "severity": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
        },
        "average": {
            "confidence": round(float(avg_confidence), 2) if avg_confidence is not None else 0.0,
            "severity": round(float(avg_severity), 2) if avg_severity is not None else 0.0,
        },
        "categories": categories,
        "defect_types": defect_types,
        "supervisor_decisions": {
            "approved": supervisor_approved,
            "rejected": supervisor_rejected,
        },
    }
