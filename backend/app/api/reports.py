from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.inspection import Inspection
from backend.app.models.product import Product
from backend.app.models.quality_result import QualityResult

router = APIRouter(
    prefix="/reports",
    tags=["Production Quality Reports"]
)


@router.get("/production")
def production_quality_report(db: Session = Depends(get_db)):
    total = db.query(func.count(Inspection.id)).scalar() or 0

    passed = (
        db.query(func.count(QualityResult.id))
        .filter(QualityResult.is_passed.is_(True))
        .scalar() or 0
    )

    failed = (
        db.query(func.count(QualityResult.id))
        .filter(QualityResult.is_passed.is_(False))
        .scalar() or 0
    )

    avg_confidence = (
        db.query(func.avg(QualityResult.confidence_score))
        .scalar() or 0
    )

    avg_severity = (
        db.query(func.avg(QualityResult.severity_score))
        .filter(QualityResult.is_passed.is_(False))
        .scalar() or 0
    )

    defects = (
        db.query(
            QualityResult.defect_type,
            func.count(QualityResult.id)
        )
        .filter(QualityResult.is_passed.is_(False))
        .group_by(QualityResult.defect_type)
        .order_by(func.count(QualityResult.id).desc())
        .all()
    )

    severity = (
        db.query(
            QualityResult.severity_level,
            func.count(QualityResult.id)
        )
        .filter(QualityResult.is_passed.is_(False))
        .group_by(QualityResult.severity_level)
        .all()
    )

    products = (
        db.query(
            Product.product_name,
            Product.product_code,
            func.count(Inspection.id)
        )
        .join(
            Inspection,
            Inspection.product_id == Product.id
        )
        .group_by(
            Product.id,
            Product.product_name,
            Product.product_code
        )
        .all()
    )

    pass_rate = (passed / total * 100) if total else 0
    defect_rate = (failed / total * 100) if total else 0

    if failed == 0:
        recommendation = "Production quality is stable. Continue routine monitoring."
    elif defect_rate >= 50:
        recommendation = (
            "High defect rate detected. Review production process, "
            "quarantine defective products, and perform detailed inspection."
        )
    else:
        recommendation = (
            "Defects detected. Continue monitoring and perform "
            "targeted quality inspection."
        )

    return {
        "report_title": "Production Quality Report",
        "summary": {
            "total_inspections": total,
            "passed_inspections": passed,
            "failed_inspections": failed,
            "pass_rate": round(pass_rate, 2),
            "defect_rate": round(defect_rate, 2),
            "average_confidence": round(float(avg_confidence), 2),
            "average_defect_severity": round(float(avg_severity), 2),
        },
        "defect_summary": [
            {
                "defect_type": defect_type,
                "count": count
            }
            for defect_type, count in defects
        ],
        "severity_summary": [
            {
                "severity_level": level,
                "count": count
            }
            for level, count in severity
        ],
        "products": [
            {
                "product_name": name,
                "product_code": code,
                "inspection_count": count
            }
            for name, code, count in products
        ],
        "quality_recommendation": recommendation,
    }