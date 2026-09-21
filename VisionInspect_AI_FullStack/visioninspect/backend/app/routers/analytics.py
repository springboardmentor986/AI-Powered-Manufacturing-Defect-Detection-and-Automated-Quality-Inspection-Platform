import datetime as dt
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import DefectRecord, InspectionImage, InspectionStatus, User
from app.schemas import AnalyticsSummary, DefectTrendPoint, DefectTypeBreakdown, SeverityBreakdown

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manufacturing Analytics Dashboard Module: defect trend analysis,
    production quality reports, inspection statistics, operational insights.
    """
    since = dt.datetime.utcnow() - dt.timedelta(days=days)
    images = db.query(InspectionImage).options(joinedload(InspectionImage.defects)).filter(
        InspectionImage.uploaded_at >= since
    ).all()

    total_images = len(images)
    pass_count = sum(1 for i in images if i.status == InspectionStatus.pass_)
    fail_count = sum(1 for i in images if i.status == InspectionStatus.fail)
    review_count = sum(1 for i in images if i.status == InspectionStatus.review)
    total_defects = sum(len(i.defects) for i in images)
    pass_rate = round((pass_count / total_images) * 100, 1) if total_images else 0.0

    type_counts = defaultdict(int)
    severity_counts = defaultdict(int)
    for i in images:
        for d in i.defects:
            type_counts[d.defect_type] += 1
            severity_counts[d.severity_level.value] += 1

    daily = defaultdict(lambda: {"total": 0, "defects": 0, "fail": 0, "pass": 0})
    for i in images:
        key = i.uploaded_at.strftime("%Y-%m-%d")
        daily[key]["total"] += 1
        daily[key]["defects"] += len(i.defects)
        if i.status == InspectionStatus.fail:
            daily[key]["fail"] += 1
        elif i.status == InspectionStatus.pass_:
            daily[key]["pass"] += 1

    trend = [
        DefectTrendPoint(
            date=day, total_inspections=v["total"], total_defects=v["defects"],
            fail_count=v["fail"], pass_count=v["pass"],
        )
        for day, v in sorted(daily.items())
    ]

    return AnalyticsSummary(
        total_images=total_images,
        total_defects=total_defects,
        pass_count=pass_count,
        fail_count=fail_count,
        review_count=review_count,
        pass_rate=pass_rate,
        defect_type_breakdown=[DefectTypeBreakdown(defect_type=k, count=v) for k, v in type_counts.items()],
        severity_breakdown=[SeverityBreakdown(severity_level=k, count=v) for k, v in severity_counts.items()],
        trend=trend,
    )
