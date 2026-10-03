"""
Milestone 3 - Manufacturing analytics: feeds the three charts on the
Analytics page (inspections over time, defect type distribution, severity
distribution).
"""
from collections import Counter, defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=schemas.AnalyticsSummary)
def summary(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    images = db.query(models.InspectionImage).all()
    status_counts = Counter(i.status for i in images)
    defects = [d for i in images for d in i.defects]
    type_counts = Counter(d.defect_type for d in defects)
    severity_counts = Counter(d.severity_level for d in defects)
    by_day = defaultdict(int)
    for i in images:
        by_day[i.uploaded_at.strftime("%Y-%m-%d")] += 1

    return schemas.AnalyticsSummary(
        total_inspections=len(images),
        pass_count=status_counts.get("pass", 0),
        fail_count=status_counts.get("fail", 0),
        review_count=status_counts.get("review", 0),
        defect_type_counts=dict(type_counts),
        severity_counts=dict(severity_counts),
        inspections_over_time=dict(sorted(by_day.items())),
    )
