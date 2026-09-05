from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.core.database import SessionLocal
from backend.app.models.product import Product
from backend.app.models.inspection import Inspection
from backend.app.models.quality_result import QualityResult
from backend.app.services.image_processing import (
    calculate_image_quality,
    detect_defect,
)

router = APIRouter(prefix="/inspection", tags=["Defect Detection"])

UPLOAD_DIR = Path("storage/uploads")
MODEL_DIR = Path("ai/models")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CATEGORIES = {
    "bottle",
    "cable",
    "screw",
    "tile",
    "toothbrush",
    "wood",
}


@router.post("/analyze")
async def analyze_image(
    category: str = Form(...),
    file: UploadFile = File(...)
):
    category = category.lower().strip()

    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Choose from: {sorted(ALLOWED_CATEGORIES)}"
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG images are allowed"
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Empty image file"
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}{extension}"
    file_path = UPLOAD_DIR / filename
    file_path.write_bytes(contents)

    model_path = MODEL_DIR / f"{category}_anomaly_model.joblib"

    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Model not found for category: {category}"
        )

    db = SessionLocal()

    try:
        # AI analysis
        quality = calculate_image_quality(str(file_path))
        prediction = detect_defect(
            str(file_path),
            str(model_path)
        )

        is_defective = prediction["is_defective"]
        confidence = prediction["confidence"]

        # Create/find product
        product_code = f"MVTEC-{category.upper()}"

        product = (
            db.query(Product)
            .filter(Product.product_code == product_code)
            .first()
        )

        if not product:
            product = Product(
                product_name=f"MVTec {category.title()}",
                product_code=product_code
            )
            db.add(product)
            db.flush()

        # Create inspection
        inspection = Inspection(
            product_id=product.id,
            image_path=str(file_path),
            status="defective" if is_defective else "passed"
        )

        db.add(inspection)
        db.flush()

        # Calculate simple severity
        if is_defective:
            severity_score = round(
                min(100, max(1, abs(prediction["anomaly_score"]) * 10000)),
                2
            )

            if severity_score >= 70:
                severity_level = "High"
            elif severity_score >= 40:
                severity_level = "Medium"
            else:
                severity_level = "Low"
        else:
            severity_score = 0.0
            severity_level = "None"

        # Create quality result
        result = QualityResult(
            inspection_id=inspection.id,
            defect_type=(
                prediction["prediction"]
                if is_defective
                else "No Defect"
            ),
            confidence_score=float(confidence),
            severity_score=severity_score,
            severity_level=severity_level,
            is_passed=not is_defective
        )

        db.add(result)
        db.commit()

        return {
            "message": "Image analysis completed",
            "category": category,
            "original_filename": file.filename,
            "stored_filename": filename,
            "inspection_id": inspection.id,
            "product_id": product.id,
            "image_quality": quality,
            "defect_detection": prediction,
            "quality_result": {
                "defect_type": result.defect_type,
                "confidence_score": result.confidence_score,
                "severity_score": result.severity_score,
                "severity_level": result.severity_level,
                "is_passed": result.is_passed
            }
        }

    except Exception as error:
        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(error)}"
        )

    finally:
        db.close()