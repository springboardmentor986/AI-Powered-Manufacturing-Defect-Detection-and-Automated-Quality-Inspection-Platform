from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, auth
from ..database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    inspections = db.query(models.Inspection).all()
    total = len(inspections)
    pass_count = sum(1 for i in inspections if i.result == "normal")
    fail_count = sum(1 for i in inspections if i.result == "defective")
    pass_rate = round((pass_count / total) * 100, 1) if total else 0
    fail_rate = round((fail_count / total) * 100, 1) if total else 0

    defects = db.query(models.Defect).all()
    severity_counts = Counter(d.severity or "unknown" for d in defects)
    type_counts = Counter(d.defect_type or "unknown" for d in defects)
    most_common_defect = type_counts.most_common(1)[0][0] if type_counts else None

    category_map = {c.category_id: c.category_name for c in db.query(models.Category).all()}
    image_category = {img.image_id: img.category_id for img in db.query(models.Image).all()}

    cat_stats = defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0})
    for insp in inspections:
        cat_id = image_category.get(insp.image_id)
        cat_name = category_map.get(cat_id, "Unknown")
        cat_stats[cat_name]["total"] += 1
        if insp.result == "normal":
            cat_stats[cat_name]["pass"] += 1
        else:
            cat_stats[cat_name]["fail"] += 1

    category_breakdown = [
        {
            "category": name,
            "total": s["total"],
            "pass": s["pass"],
            "fail": s["fail"],
            "fail_rate": round((s["fail"] / s["total"]) * 100, 1) if s["total"] else 0,
        }
        for name, s in sorted(cat_stats.items(), key=lambda x: -x[1]["total"])
    ]

    trend_map = defaultdict(lambda: {"total": 0, "defective": 0})
    for insp in inspections:
        day = insp.inspection_time.date().isoformat() if insp.inspection_time else "unknown"
        trend_map[day]["total"] += 1
        if insp.result == "defective":
            trend_map[day]["defective"] += 1
    trend = [{"date": d, **v} for d, v in sorted(trend_map.items())]

    return {
        "total_inspections": total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_rate,
        "fail_rate": fail_rate,
        "most_common_defect": most_common_defect,
        "severity_breakdown": [
            {"severity": s, "count": c} for s, c in severity_counts.items()
        ],
        "defect_type_breakdown": [
            {"type": t, "count": c} for t, c in type_counts.most_common(8)
        ],
        "category_breakdown": category_breakdown,
        "trend": trend,
    }
