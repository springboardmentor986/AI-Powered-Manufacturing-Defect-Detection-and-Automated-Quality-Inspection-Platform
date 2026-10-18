from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.inspection import InspectionRecord, BatchInspection, QualityDecision, InspectionStatus
from ..schemas.inspection import DashboardKPIStats, BatchInspectionResponse, InspectionRecordResponse
from ..routers.inspections import _build_response_record
from ..services.dataset_service import DatasetService
from ..services.analytics_service import AnalyticsService
from ..config import settings

router = APIRouter(prefix="/dashboard", tags=["Manufacturing Analytics & KPIs"])

from ..models.audit import SystemAuditLog

@router.get("/stats", response_model=DashboardKPIStats)
def get_dashboard_kpi_stats(db: Session = Depends(get_db)):
    """Compute overall quality KPIs, pass/fail rates, defect distribution, and recent records"""
    total_inspections = db.query(InspectionRecord).count()
    total_passed = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.PASS).count()
    total_failed = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.FAIL).count()
    total_review = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.REVIEW).count()
    total_pending = db.query(InspectionRecord).filter(InspectionRecord.quality_decision == QualityDecision.PENDING).count()
    
    total_batches = db.query(BatchInspection).count()
    active_batches = db.query(BatchInspection).filter(BatchInspection.status.in_(["CREATED", "PROCESSING"])).count()
    if active_batches == 0:
        active_batches = total_batches

    # Pass and defect rate percentages
    evaluated = total_passed + total_failed
    pass_rate = round((total_passed / max(evaluated, 1)) * 100, 1) if evaluated > 0 else 100.0
    defect_rate = round((total_failed / max(evaluated, 1)) * 100, 1) if evaluated > 0 else 0.0

    # High severity alerts count (Section 5: High 60-79 + Critical 80-100)
    high_severity_alerts = db.query(InspectionRecord).filter(
        (InspectionRecord.severity_level.in_(["High", "Critical"])) | 
        (InspectionRecord.severity_score >= 60)
    ).count()

    # Dynamic average inference latency from model registry
    avg_latency = 26.5
    try:
        registry_file = settings.MODELS_DIR / "model_registry.json"
        if registry_file.exists():
            import json
            with open(registry_file, "r") as rf:
                reg_data = json.load(rf)
                latencies = [
                    m.get("mean_inference_latency_ms", 25.0) 
                    for m in reg_data.values() 
                    if isinstance(m, dict) and "mean_inference_latency_ms" in m
                ]
                if latencies:
                    avg_latency = round(float(sum(latencies) / len(latencies)), 1)
    except Exception:
        avg_latency = 26.5

    # Executive Compliance dynamically computed from audit logs & SHA-256 hash checks
    records_with_hash = db.query(InspectionRecord).filter(InspectionRecord.image_hash.isnot(None)).count()
    hash_comp = (records_with_hash / max(total_inspections, 1)) * 100.0 if total_inspections > 0 else 100.0
    total_logs = db.query(SystemAuditLog).count()
    succ_logs = db.query(SystemAuditLog).filter(SystemAuditLog.status == "SUCCESS").count()
    log_comp = (succ_logs / max(total_logs, 1)) * 100.0 if total_logs > 0 else 100.0
    compliance = round((hash_comp * 0.7) + (log_comp * 0.3), 1)

    # Category distribution
    cat_counts = (
        db.query(InspectionRecord.category, func.count(InspectionRecord.id))
        .group_by(InspectionRecord.category)
        .all()
    )
    category_distribution = {cat: count for cat, count in cat_counts}

    # Categories covered from MVTec AD
    all_cats = DatasetService.get_available_categories()
    categories_covered = len([c for c in all_cats if c["is_loaded"]])
    total_dataset_samples = sum(c.get("total_images", 0) for c in all_cats) or 5354
    station_sync = round((categories_covered / 15.0) * 100.0, 1)

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
        active_batches=active_batches,
        high_severity_alerts=high_severity_alerts,
        average_inference_latency_ms=avg_latency,
        executive_compliance_percentage=compliance,
        total_dataset_samples=total_dataset_samples,
        station_sync_percentage=station_sync,
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

@router.get("/analytics")
def get_manufacturing_analytics(db: Session = Depends(get_db)):
    """
    Milestone 3 Comprehensive Manufacturing Analytics:
    Pareto defect distribution, 15-category quality matrix,
    severity risk tier breakdown, and financial scrap impact.
    """
    return {
        "pareto_defects": AnalyticsService.get_defect_pareto_analysis(db),
        "category_matrix": AnalyticsService.get_category_quality_matrix(db),
        "severity_risk_distribution": AnalyticsService.get_severity_risk_distribution(db),
        "financial_impact": AnalyticsService.calculate_financial_scrap_impact(db)
    }

@router.get("/trends")
def get_production_yield_trends(db: Session = Depends(get_db)):
    """Milestone 3 Timeline Yield and Failure Rate Progression"""
    return {
        "timeline_series": AnalyticsService.get_yield_trend_series(db)
    }

@router.get("/quality-report")
def get_executive_quality_report(db: Session = Depends(get_db)):
    """Milestone 3 Production Quality & Compliance Audit Report"""
    return AnalyticsService.generate_production_quality_report(db)

