import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import InspectionImage, InspectionStatus, User
from app.schemas import InspectionImageOut, InspectionImageSummary

router = APIRouter(prefix="/api/inspections", tags=["inspections"])


@router.get("", response_model=List[InspectionImageSummary])
def list_inspections(
    status_filter: Optional[InspectionStatus] = Query(None, alias="status"),
    product_line: Optional[str] = None,
    batch_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Inspection reporting: list inspections with optional filters."""
    q = db.query(InspectionImage).options(joinedload(InspectionImage.defects))
    if status_filter:
        q = q.filter(InspectionImage.status == status_filter)
    if product_line:
        q = q.filter(InspectionImage.product_line == product_line)
    if batch_id:
        q = q.filter(InspectionImage.batch_id == batch_id)
    records = q.order_by(InspectionImage.uploaded_at.desc()).limit(limit).all()

    summaries = []
    for r in records:
        max_sev = None
        order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        for d in r.defects:
            if max_sev is None or order.get(d.severity_level.value, 0) > order.get(max_sev, 0):
                max_sev = d.severity_level.value
        summaries.append(InspectionImageSummary(
            id=r.id, filename=r.filename, status=r.status,
            uploaded_at=r.uploaded_at, defect_count=len(r.defects),
            max_severity=max_sev,
        ))
    return summaries


@router.get("/{image_id}", response_model=InspectionImageOut)
def get_inspection(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(InspectionImage).options(joinedload(InspectionImage.defects)).filter(
        InspectionImage.id == image_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return record


@router.get("/export/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export Data (CSV) -- Outputs & Actions from the architecture diagram."""
    records = db.query(InspectionImage).options(joinedload(InspectionImage.defects)).order_by(
        InspectionImage.uploaded_at.desc()
    ).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "image_id", "filename", "product_line", "batch_id", "uploaded_at", "status",
        "defect_type", "severity_score", "severity_level",
    ])
    for r in records:
        if not r.defects:
            writer.writerow([r.id, r.filename, r.product_line, r.batch_id, r.uploaded_at, r.status.value, "", "", ""])
        for d in r.defects:
            writer.writerow([
                r.id, r.filename, r.product_line, r.batch_id, r.uploaded_at, r.status.value,
                d.defect_type, d.severity_score, d.severity_level.value,
            ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inspection_report.csv"},
    )
