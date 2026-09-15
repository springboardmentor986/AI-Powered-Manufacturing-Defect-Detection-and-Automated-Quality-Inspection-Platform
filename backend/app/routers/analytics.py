from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import Date, Float, case, cast, func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.image import Image
from app.security.authorization import require_role
from app.security.dependencies import get_current_user
from app.services.report_service import generate_production_quality_report_csv

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/trends")
def get_analytics_trends(
    days: str = Query("30", pattern="^(7|30|all)$"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(2)),
):
    days_clean = days.lower()
    today = datetime.now(timezone.utc).date()

    query = (
        db.query(
            cast(Image.uploaded_at, Date).label("day"),
            func.count(Image.id).label("total"),
            func.sum(case((Image.quality_decision == "Accept", 1), else_=0)).label("accepted"),
            func.sum(case((Image.quality_decision == "Reject", 1), else_=0)).label("rejected"),
            func.avg(cast(Image.severity_score, Float)).label("avg_severity"),
        )
        .filter(Image.severity_score.isnot(None))
    )

    if days_clean in ("7", "30"):
        num_days = int(days_clean)
        start_date = today - timedelta(days=num_days - 1)
        query = query.filter(cast(Image.uploaded_at, Date) >= start_date)
        end_date = today
    else:
        start_date = None
        end_date = today

    results = (
        query.group_by(cast(Image.uploaded_at, Date))
        .order_by(cast(Image.uploaded_at, Date).asc())
        .all()
    )

    data_by_date = {
        r.day.strftime("%Y-%m-%d"): {
            "date": r.day.strftime("%Y-%m-%d"),
            "total_inspections": int(r.total or 0),
            "accepted": int(r.accepted or 0),
            "rejected": int(r.rejected or 0),
            "defect_rate": (
                round((float(r.rejected or 0) / float(r.total) * 100.0), 2)
                if r.total
                else 0.0
            ),
            "avg_severity": (
                round(float(r.avg_severity), 2)
                if r.avg_severity is not None
                else 0.0
            ),
        }
        for r in results
    }

    if days_clean == "all":
        if not results:
            return []
        start_date = results[0].day
        end_date = max(results[-1].day, today)

    trend_list = []
    curr = start_date
    while curr <= end_date:
        d_str = curr.strftime("%Y-%m-%d")
        if d_str in data_by_date:
            trend_list.append(data_by_date[d_str])
        else:
            trend_list.append({
                "date": d_str,
                "total_inspections": 0,
                "accepted": 0,
                "rejected": 0,
                "defect_rate": 0.0,
                "avg_severity": 0.0,
            })
        curr += timedelta(days=1)

    return trend_list


@router.get("/reports/export")
def export_production_quality_report(
    format: str = Query("csv", pattern="^(csv)$"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(2)),
):
    if format.lower() != "csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: '{format}'. Only 'csv' is supported.",
        )

    csv_data = generate_production_quality_report_csv(db)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"production_quality_report_{timestamp}.csv"

    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


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
