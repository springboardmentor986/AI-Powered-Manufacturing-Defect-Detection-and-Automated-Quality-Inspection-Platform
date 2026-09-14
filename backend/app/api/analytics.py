from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.inspection import Inspection
from backend.app.models.product import Product
from backend.app.models.quality_result import QualityResult


router = APIRouter(
    prefix="/analytics",
    tags=["Manufacturing Analytics"]
)


@router.get("/summary")
def analytics_summary(
    db: Session = Depends(get_db)
):
    """
    Overall manufacturing inspection statistics.
    """

    total_inspections = (
        db.query(func.count(Inspection.id))
        .scalar()
        or 0
    )

    passed_inspections = (
        db.query(func.count(QualityResult.id))
        .filter(QualityResult.is_passed.is_(True))
        .scalar()
        or 0
    )

    failed_inspections = (
        db.query(func.count(QualityResult.id))
        .filter(QualityResult.is_passed.is_(False))
        .scalar()
        or 0
    )

    if total_inspections > 0:
        pass_rate = round(
            (passed_inspections / total_inspections) * 100,
            2
        )

        defect_rate = round(
            (failed_inspections / total_inspections) * 100,
            2
        )
    else:
        pass_rate = 0.0
        defect_rate = 0.0

    average_confidence = (
        db.query(
            func.avg(
                QualityResult.confidence_score
            )
        )
        .scalar()
    )

    average_severity = (
        db.query(
            func.avg(
                QualityResult.severity_score
            )
        )
        .filter(
            QualityResult.is_passed.is_(False)
        )
        .scalar()
    )

    return {
        "total_inspections": total_inspections,
        "passed_inspections": passed_inspections,
        "failed_inspections": failed_inspections,
        "pass_rate": pass_rate,
        "defect_rate": defect_rate,
        "average_confidence": round(
            float(average_confidence or 0),
            2
        ),
        "average_defect_severity": round(
            float(average_severity or 0),
            2
        )
    }


@router.get("/defects")
def defect_distribution(
    db: Session = Depends(get_db)
):
    """
    Distribution of detected defect types.
    """

    rows = (
        db.query(
            QualityResult.defect_type,
            func.count(QualityResult.id)
        )
        .filter(
            QualityResult.is_passed.is_(False)
        )
        .group_by(
            QualityResult.defect_type
        )
        .order_by(
            func.count(QualityResult.id).desc()
        )
        .all()
    )

    return {
        "defects": [
            {
                "defect_type": defect_type,
                "count": count
            }
            for defect_type, count in rows
        ]
    }


@router.get("/severity")
def severity_distribution(
    db: Session = Depends(get_db)
):
    """
    Distribution of defect severity levels.
    """

    rows = (
        db.query(
            QualityResult.severity_level,
            func.count(QualityResult.id)
        )
        .filter(
            QualityResult.is_passed.is_(False)
        )
        .group_by(
            QualityResult.severity_level
        )
        .all()
    )

    return {
        "severity": [
            {
                "severity_level": severity_level,
                "count": count
            }
            for severity_level, count in rows
        ]
    }


@router.get("/products")
def product_statistics(
    db: Session = Depends(get_db)
):
    """
    Inspection statistics grouped by product.
    """

    rows = (
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
        .order_by(
            func.count(Inspection.id).desc()
        )
        .all()
    )

    result = []

    for product_name, product_code, count in rows:

        failed = (
            db.query(func.count(QualityResult.id))
            .join(
                Inspection,
                Inspection.id ==
                QualityResult.inspection_id
            )
            .filter(
                Inspection.product_id ==
                db.query(Product.id)
                .filter(
                    Product.product_code ==
                    product_code
                )
                .scalar_subquery()
            )
            .filter(
                QualityResult.is_passed.is_(False)
            )
            .scalar()
            or 0
        )

        product_pass_rate = round(
            ((count - failed) / count) * 100,
            2
        ) if count else 0.0

        result.append(
            {
                "product_name": product_name,
                "product_code": product_code,
                "total_inspections": count,
                "failed_inspections": failed,
                "pass_rate": product_pass_rate
            }
        )

    return {
        "products": result
    }


@router.get("/recent")
def recent_inspections(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Most recent inspection records.
    """

    limit = max(
        1,
        min(limit, 100)
    )

    rows = (
        db.query(
            Inspection,
            Product,
            QualityResult
        )
        .join(
            Product,
            Inspection.product_id ==
            Product.id
        )
        .outerjoin(
            QualityResult,
            Inspection.id ==
            QualityResult.inspection_id
        )
        .order_by(
            Inspection.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    inspections = []

    for inspection, product, quality in rows:

        inspections.append(
            {
                "inspection_id": inspection.id,
                "product_name": product.product_name,
                "product_code": product.product_code,
                "status": inspection.status,
                "created_at": (
                    inspection.created_at.isoformat()
                    if inspection.created_at
                    else None
                ),
                "defect_type": (
                    quality.defect_type
                    if quality
                    else None
                ),
                "confidence_score": (
                    quality.confidence_score
                    if quality
                    else None
                ),
                "severity_score": (
                    quality.severity_score
                    if quality
                    else None
                ),
                "severity_level": (
                    quality.severity_level
                    if quality
                    else None
                ),
                "is_passed": (
                    quality.is_passed
                    if quality
                    else None
                )
            }
        )

    return {
        "inspections": inspections
    }


@router.get("/trends")
def inspection_trends(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Daily inspection and defect trend data.
    """

    days = max(
        1,
        min(days, 90)
    )

    start_date = datetime.utcnow() - timedelta(
        days=days - 1
    )

    rows = (
        db.query(
            func.date(Inspection.created_at),
            func.count(Inspection.id)
        )
        .filter(
            Inspection.created_at >= start_date
        )
        .group_by(
            func.date(Inspection.created_at)
        )
        .order_by(
            func.date(Inspection.created_at)
        )
        .all()
    )

    defect_rows = (
        db.query(
            func.date(Inspection.created_at),
            func.count(QualityResult.id)
        )
        .join(
            QualityResult,
            Inspection.id ==
            QualityResult.inspection_id
        )
        .filter(
            Inspection.created_at >= start_date
        )
        .filter(
            QualityResult.is_passed.is_(False)
        )
        .group_by(
            func.date(Inspection.created_at)
        )
        .order_by(
            func.date(Inspection.created_at)
        )
        .all()
    )

    inspection_map = {
        str(date): count
        for date, count in rows
    }

    defect_map = {
        str(date): count
        for date, count in defect_rows
    }

    result = []

    for i in range(days):

        current_date = (
            datetime.utcnow()
            - timedelta(days=days - 1 - i)
        ).date()

        date_key = str(current_date)

        result.append(
            {
                "date": date_key,
                "inspections": (
                    inspection_map.get(
                        date_key,
                        0
                    )
                ),
                "defects": (
                    defect_map.get(
                        date_key,
                        0
                    )
                )
            }
        )

    return {
        "days": days,
        "trends": result
    }