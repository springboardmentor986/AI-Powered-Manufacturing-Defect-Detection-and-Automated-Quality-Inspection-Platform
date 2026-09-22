from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, auth
from ..database import get_db
from ..vision import detector, preprocessing

router = APIRouter(prefix="/inspections", tags=["Inspections"])

# Rough severity weight per defect-type keyword (0-100). Matched by
# substring against the resolved defect type label. This is a heuristic
# lookup, not a trained classifier — it lets the 'Defect Type (25%)'
# term in the project's severity formula reflect something meaningful
# even without per-type training data.
TYPE_SEVERITY = {
    "crack": 90,
    "break": 90,
    "broken": 90,
    "missing": 90,
    "hole": 85,
    "bent": 75,
    "cut": 75,
    "thread": 70,
    "liquid": 70,
    "fold": 65,
    "poke": 60,
    "metal_contamination": 65,
    "scratch": 55,
    "contamination": 55,
    "color": 50,
    "squeeze": 50,
    "rough": 45,
    "glue": 50,
}
DEFAULT_TYPE_SEVERITY = 60


def _resolve_defect_type(image: models.Image) -> str:
    """
    If this image came from the MVTec dataset with a known defect
    category (encoded as 'test_defect:<label>' by
    update_defect_labels.py), use that specific label. Otherwise fall
    back to a generic 'anomaly' tag — manually uploaded images have no
    ground-truth defect type, since fine-grained classification of an
    unseen image would require a trained classifier (a natural next
    step beyond this milestone).
    """
    if image.image_type and image.image_type.startswith("test_defect:"):
        label = image.image_type.split(":", 1)[1]
        return label.replace("_", " ")
    return "anomaly"


def _type_score(defect_type: str) -> float:
    label = defect_type.lower()
    for keyword, score in TYPE_SEVERITY.items():
        if keyword in label:
            return score
    return DEFAULT_TYPE_SEVERITY


def _severity_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


@router.post("/run/{image_id}")
def run_inspection(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    image = db.query(models.Image).filter(models.Image.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    category = (
        db.query(models.Category)
        .filter(models.Category.category_id == image.category_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=400, detail="Image has no category")

    if not detector.has_reference(category.category_name):
        raise HTTPException(
            status_code=400,
            detail=(
                f"No trained reference for category '{category.category_name}'. "
                f"Run build_references.py on the backend first."
            ),
        )

    try:
        prediction = detector.predict(image.image_path, category.category_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inspection failed: {e}")

    raw_img = preprocessing.load_image(image.image_path)
    quality = preprocessing.quality_report(raw_img)

    inspection = models.Inspection(
        image_id=image.image_id,
        inspected_by=current_user.user_id,
        status="completed",
        result=prediction["result"],
        confidence_score=prediction["confidence_score"],
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    severity_breakdown = None
    defect_type = None
    severity_level = None

    if prediction["result"] == "defective":
        defect_type = _resolve_defect_type(image)
        type_score = _type_score(defect_type)

        # Project severity formula: Size(30%) + Location(25%) + Type(25%) + Confidence(20%)
        severity_score = round(
            prediction["size_score"] * 0.30
            + prediction["location_score"] * 0.25
            + type_score * 0.25
            + prediction["confidence_score"] * 0.20,
            2,
        )
        severity_level = _severity_level(severity_score)

        severity_breakdown = {
            "size_score": prediction["size_score"],
            "location_score": prediction["location_score"],
            "type_score": type_score,
            "confidence_score": prediction["confidence_score"],
            "severity_score": severity_score,
            "patch_location": prediction["patch_location"],
        }

        defect = models.Defect(
            inspection_id=inspection.inspection_id,
            defect_type=defect_type,
            severity=severity_level,
            location_data=severity_breakdown,
        )
        db.add(defect)
        db.commit()

    return {
        "inspection_id": inspection.inspection_id,
        "result": prediction["result"],
        "confidence_score": prediction["confidence_score"],
        "defect_type": defect_type,
        "severity": severity_level,
        "severity_breakdown": severity_breakdown,
        "quality": quality,
    }
