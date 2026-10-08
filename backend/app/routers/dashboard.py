from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.inspection import InspectionRecord, BatchInspection, QualityDecision, InspectionStatus
from ..schemas.inspection import DashboardKPIStats, BatchInspectionResponse, InspectionRecordResponse
from ..routers.inspections import _build_response_record
from ..services.dataset_service import DatasetService
from ..config import settings

router = APIRouter(prefix="/dashboard", tags=["Manufacturing Analytics & KPIs"])

@router.get("/stats", response_model=DashboardKPIStats)
def get_dashboard_kpi_stats(db: Session = Depends(get_db)):
    """Compute overall quality KPIs, pass/fail rates, defect distribution, and recent records"""
    total_inspections = db.query(InspectionRecord).count()
    total_passed = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.PASS).count()
    total_failed = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.FAIL).count()
    total_review = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.REVIEW).count()
    total_pending = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.PENDING).count()
    
    total_batches = db.query(BatchInspection).count()

    # Pass and defect rate percentages
    evaluated = total_passed + total_failed
    pass_rate = round((total_passed / max(evaluated, 1)) * 100, 1) if evaluated > 0 else 100.0
    defect_rate = round((total_failed / max(evaluated, 1)) * 100, 1) if evaluated > 0 else 0.0

    # Category distribution
    cat_counts = (
        db.query(InspectionRecord.category, func.count(InspectionRecord.id))
        .group_by(InspectionRecord.category)
        .all()
    )
    category_distribution = {cat: count for cat, count in cat_counts}

    # Categories covered from MVTec AD
    categories_covered = len([c for c in DatasetService.get_available_categories() if c["is_loaded"]])

    # Recent inspections
    recent_records = (
        db.query(InspectionRecord)
        .order_by(InspectionRecord.created_at.desc())
        .limit(8)
        .all()
    )

    return DashboardKPIStats(
        total_inspections=total_inspections,
        total_passed=total_passed,
        total_failed=total_failed,
        total_review=total_review,
        total_pending=total_pending,
        pass_rate_percentage=pass_rate,
        defect_rate_percentage=defect_rate,
        total_batches=total_batches,
        categories_covered=categories_covered,
        system_status="OPERATIONAL",
        category_distribution=category_distribution,
        recent_inspections=[_build_response_record(r) for r in recent_records]
    )

@router.get("/batches", response_model=List[BatchInspectionResponse])
def list_batches(db: Session = Depends(get_db)):
    """List recent inspection batches"""
    batches = db.query(BatchInspection).order_by(BatchInspection.created_at.desc()).limit(20).all()
    return [
        BatchInspectionResponse(
            id=b.id,
            batch_name=b.batch_name,
            description=b.description,
            category=b.category,
            total_images=b.total_images,
            processed_images=b.processed_images,
            pass_count=b.pass_count,
            fail_count=b.fail_count,
            review_count=b.review_count,
            status=b.status,
            created_by=b.created_by,
            creator_name=b.creator.full_name if b.creator else "System",
            created_at=b.created_at,
            updated_at=b.updated_at
        )
        for b in batches
    ]
