from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.core.database import SessionLocal
from backend.app.models.inspection import Inspection
from backend.app.models.product import Product
from backend.app.models.quality_result import QualityResult

from backend.app.services.defect_classification import (
    classify_defect,
    get_defect_type_score,
)

from backend.app.services.image_processing import (
    calculate_image_quality,
    detect_defect,
)

from backend.app.services.severity_scoring import (
    calculate_quality_decision,
    calculate_severity,
)


router = APIRouter(
    prefix="/inspection",
    tags=["Defect Detection"],
)


# ============================================================
# DIRECTORIES
# ============================================================

UPLOAD_DIR = Path("storage/uploads")
MODEL_DIR = Path("ai/models")


# ============================================================
# ALLOWED FILE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


# ============================================================
# ALL 15 MVTec AD CATEGORIES
# ============================================================

ALLOWED_CATEGORIES = {
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper",
}


# ============================================================
# BASELINE SIZE SCORE
# ============================================================

def calculate_size_score(
    anomaly_score: float,
    is_defective: bool,
) -> float:
    """
    Baseline defect-size contribution.

    The current anomaly detector does not yet produce
    a segmentation mask, so true pixel-level defect
    size is not available.

    This is a temporary baseline score.
    """

    if not is_defective:
        return 0.0

    strength = min(
        1.0,
        abs(float(anomaly_score)) * 10,
    )

    return round(
        40.0 + (strength * 60.0),
        2,
    )


# ============================================================
# BASELINE LOCATION SCORE
# ============================================================

def calculate_location_score(
    is_defective: bool,
) -> float:
    """
    Baseline defect-location contribution.

    True location scoring will be implemented when
    defect localization is added.
    """

    if not is_defective:
        return 0.0

    return 50.0


# ============================================================
# IMAGE ANALYSIS ENDPOINT
# ============================================================

@router.post("/analyze")
async def analyze_image(
    category: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Complete VisionInspect AI inspection pipeline.

    Pipeline:

        Upload
          ↓
        Image Quality
          ↓
        AI Anomaly Detection
          ↓
        Defect Classification
          ↓
        Severity Scoring
          ↓
        Quality Decision
          ↓
        PostgreSQL
    """

    # ========================================================
    # 1. VALIDATE CATEGORY
    # ========================================================

    category = category.lower().strip()

    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid category. Choose from: "
                f"{sorted(ALLOWED_CATEGORIES)}"
            ),
        )

    # ========================================================
    # 2. VALIDATE FILE
    # ========================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, JPEG and PNG images are allowed"
            ),
        )

    # ========================================================
    # 3. READ IMAGE
    # ========================================================

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Empty image file",
        )

    # ========================================================
    # 4. SAVE UPLOADED IMAGE
    # ========================================================

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"{uuid4()}{extension}"

    file_path = UPLOAD_DIR / filename

    file_path.write_bytes(contents)

    # ========================================================
    # 5. FIND CATEGORY MODEL
    # ========================================================

    model_path = (
        MODEL_DIR
        / category
        / "model_package.joblib"
    )

    if not model_path.exists():

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=404,
            detail=(
                f"Model package not found for category: "
                f"{category}"
            ),
        )

    # ========================================================
    # DATABASE SESSION
    # ========================================================

    db = SessionLocal()

    try:

        # ====================================================
        # 6. IMAGE QUALITY ANALYSIS
        # ====================================================

        quality = calculate_image_quality(
            str(file_path)
        )

        # ====================================================
        # 7. AI ANOMALY DETECTION
        # ====================================================

        prediction = detect_defect(
            str(file_path),
            str(model_path),
        )

        is_defective = bool(
            prediction["is_defective"]
        )

        confidence = float(
            prediction["confidence"]
        )

        anomaly_score = float(
            prediction["anomaly_score"]
        )

        # ====================================================
        # 8. DEFECT CLASSIFICATION
        # ====================================================

        classification = classify_defect(
            category=category,
            is_defective=is_defective,
            anomaly_score=anomaly_score,
        )

        defect_type = classification[
            "defect_type"
        ]

        classification_confidence = float(
            classification[
                "classification_confidence"
            ]
        )

        # ====================================================
        # 9. SEVERITY INPUT SCORES
        # ====================================================

        size_score = calculate_size_score(
            anomaly_score,
            is_defective,
        )

        location_score = calculate_location_score(
            is_defective,
        )

        defect_type_score = (
            get_defect_type_score(
                defect_type
            )
        )

        # ====================================================
        # 10. SEVERITY CALCULATION
        # ====================================================

        severity = calculate_severity(
            defect_size_score=size_score,
            defect_location_score=location_score,
            defect_type_score=defect_type_score,
            confidence_score=confidence,
        )

        severity_score = float(
            severity["severity_score"]
        )

        severity_level = severity[
            "severity_level"
        ]

        # ====================================================
        # 11. QUALITY CONTROL DECISION
        # ====================================================

        quality_decision = calculate_quality_decision(
            is_defective=is_defective,
            severity_score=severity_score,
        )

        # ====================================================
        # 12. CREATE / FIND PRODUCT
        # ====================================================

        product_code = (
            f"MVTEC-{category.upper()}"
        )

        product = (
            db.query(Product)
            .filter(
                Product.product_code
                == product_code
            )
            .first()
        )

        if not product:

            product = Product(
                product_name=(
                    f"MVTec {category.title()}"
                ),
                product_code=product_code,
            )

            db.add(product)
            db.flush()

        # ====================================================
        # 13. CREATE INSPECTION
        # ====================================================

        inspection = Inspection(
            product_id=product.id,
            image_path=str(file_path),
            status=(
                "passed"
                if quality_decision["is_passed"]
                else "defective"
            ),
        )

        db.add(inspection)
        db.flush()

        # ====================================================
        # 14. CREATE QUALITY RESULT
        # ====================================================

        result = QualityResult(
            inspection_id=inspection.id,
            defect_type=defect_type,
            confidence_score=confidence,
            severity_score=severity_score,
            severity_level=severity_level,
            is_passed=quality_decision[
                "is_passed"
            ],
        )

        db.add(result)

        # ====================================================
        # 15. SAVE DATABASE CHANGES
        # ====================================================

        db.commit()

        # ====================================================
        # 16. RESPONSE
        # ====================================================

        return {
            "message": "Image analysis completed",

            "category": category,

            "original_filename": file.filename,

            "stored_filename": filename,

            "inspection_id": inspection.id,

            "product_id": product.id,

            "model": {
                "model_path": str(model_path),
                "model_type": "Isolation Forest",
            },

            "image_quality": quality,

            "defect_detection": prediction,

            "defect_classification": {
                "category": classification[
                    "category"
                ],

                "defect_type": defect_type,

                "classification_confidence": (
                    classification_confidence
                ),

                "classification_method": (
                    classification[
                        "classification_method"
                    ]
                ),
            },

            "severity_assessment": {
                "defect_size_score": (
                    severity[
                        "defect_size_score"
                    ]
                ),

                "defect_location_score": (
                    severity[
                        "defect_location_score"
                    ]
                ),

                "defect_type_score": (
                    severity[
                        "defect_type_score"
                    ]
                ),

                "confidence_score": (
                    severity[
                        "confidence_score"
                    ]
                ),

                "severity_score": severity_score,

                "severity_level": severity_level,
            },

            "quality_result": {
                "defect_type": defect_type,

                "confidence_score": confidence,

                "severity_score": severity_score,

                "severity_level": severity_level,

                "is_passed": quality_decision[
                    "is_passed"
                ],

                "decision": quality_decision[
                    "decision"
                ],

                "risk_level": quality_decision[
                    "risk_level"
                ],

                "recommendation": quality_decision[
                    "recommendation"
                ],
            },
        }

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except HTTPException:

        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise

    except Exception as error:

        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                "Image analysis failed: "
                f"{str(error)}"
            ),
        )

    finally:

        db.close()