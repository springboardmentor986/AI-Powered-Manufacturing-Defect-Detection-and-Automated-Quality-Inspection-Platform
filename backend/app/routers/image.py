import sys
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.image_schema import ImageReviewRequest
from app.schemas.inspection_schema import InspectionRequest
from app.security.authorization import require_any_role, require_role
from app.services.image_service import (
    BASE_DIR,
    create_image_record,
    generate_stored_filename,
    get_all_images,
    get_image_by_id,
    review_image,
    save_image,
    validate_file_size,
    validate_file_type,
    validate_image_content,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.models.inspection_pipeline import InspectionPipeline

router = APIRouter(prefix="/images", tags=["Images"])

AI_DIR = PROJECT_ROOT / "ai"
INSPECTION_RESULTS_DIR = PROJECT_ROOT / "inspection_results"
INSPECTION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

inspection_pipeline = InspectionPipeline(
    normal_features_path=str(AI_DIR / "models/normal_features_layer3.pt"),
    confidence_scores_path=str(AI_DIR / "evaluation/confidence_scores.csv"),
    size_boundaries_path=str(AI_DIR / "models/size_score_boundaries.csv"),
    segmentation_model_path=str(AI_DIR / "models/defect_segmenter_unet.pt"),
    segmentation_threshold_path=str(AI_DIR / "models/segmentation_threshold.txt"),
    anomaly_thresholds_path=str(AI_DIR / "models/anomaly_thresholds.csv"),
    postprocessing_config_path=str(AI_DIR / "models/segmentation_postprocessing.json"),
)


def create_defect_overlay(image_path: Path, segmentation_mask: np.ndarray, output_path: Path) -> None:
    """Generates a visual defect contour overlay on the original image."""
    original_image = cv2.imread(str(image_path))
    if original_image is None:
        raise ValueError("Unable to read original image for overlay")

    height, width = original_image.shape[:2]
    mask = cv2.resize(
        np.asarray(segmentation_mask, dtype=np.uint8),
        (width, height),
        interpolation=cv2.INTER_NEAREST,
    )
    mask = np.where(mask > 0, 255, 0).astype(np.uint8)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # For confirmed normal specimens without defect pixels, write original image cleanly
    if np.sum(mask > 0) == 0:
        if not cv2.imwrite(str(output_path), original_image):
            raise ValueError("Failed to save defect overlay")
        return

    overlay = np.zeros_like(original_image)
    overlay[:, :, 2] = 255  # Red highlight channel (BGR)

    highlighted = original_image.copy()
    defect_pixels = mask > 0
    highlighted[defect_pixels] = cv2.addWeighted(
        original_image[defect_pixels], 0.45, overlay[defect_pixels], 0.55, 0
    )

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(highlighted, contours, -1, (0, 0, 255), 2)

    if not cv2.imwrite(str(output_path), highlighted):
        raise ValueError("Failed to save defect overlay")


def serialize_image(db: Session, image) -> dict:
    uploader = db.query(User).filter(User.id == image.uploaded_by).first()
    reviewer = db.query(User).filter(User.id == image.reviewed_by).first() if image.reviewed_by else None
    overlay_path = INSPECTION_RESULTS_DIR / f"{image.id}_defect_overlay.png"

    return {
        "id": image.id,
        "original_filename": image.original_filename,
        "stored_filename": image.stored_filename,
        "storage_path": image.storage_path,
        "uploaded_by": {
            "id": uploader.id,
            "name": uploader.name,
            "email": uploader.email,
        } if uploader else None,
        "uploaded_at": image.uploaded_at,
        "inspection_status": image.inspection_status,
        "supervisor_decision": image.supervisor_decision,
        "supervisor_notes": image.supervisor_notes,
        "reviewed_by": {
            "id": reviewer.id,
            "name": reviewer.name,
            "email": reviewer.email,
        } if reviewer else None,
        "reviewed_at": image.reviewed_at,
        "category": image.category,
        "defect_type": image.defect_type,
        "predicted_category": getattr(image, "predicted_category", image.category),
        "predicted_defect_type": getattr(image, "predicted_defect_type", image.defect_type),
        "resolved_defect_status": getattr(image, "resolved_defect_status", image.defect_type),
        "inspection_decision": "NORMAL" if (image.quality_decision == "Accept" or image.defect_type == "normal") else "DEFECTIVE",
        "classification_confidence": getattr(image, "classification_confidence", None),
        "anomaly_score": image.anomaly_score,
        "confidence_score": image.confidence_score,
        "predicted_area_percent": image.predicted_area_percent,
        "size_score": image.size_score,
        "location_score": image.location_score,
        "defect_type_score": image.defect_type_score,
        "severity_score": image.severity_score,
        "severity_level": image.severity_level,
        "quality_decision": image.quality_decision,
        "inspection_overlay_available": overlay_path.exists(),
    }


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user=Depends(require_role(1)),
    db: Session = Depends(get_db),
):
    storage_path = None
    try:
        validate_file_type(file.content_type)
        await validate_file_size(file)
        validate_image_content(file)

        stored_filename = generate_stored_filename(current_user["user_id"], file.filename)
        storage_path = await save_image(file, stored_filename)
        image = create_image_record(
            db=db,
            original_filename=file.filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            uploaded_by=current_user["user_id"],
        )

        return {
            "id": image.id,
            "original_filename": image.original_filename,
            "stored_filename": image.stored_filename,
            "storage_path": image.storage_path,
            "uploaded_by": image.uploaded_by,
            "uploaded_at": image.uploaded_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError:
        db.rollback()
        if storage_path is not None:
            (BASE_DIR / storage_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image information",
        )


@router.post("/{image_id}/inspect")
def inspect_image(
    image_id: int,
    inspection_data: InspectionRequest = InspectionRequest(),
    current_user=Depends(require_role(1)),
    db: Session = Depends(get_db),
):
    image = get_image_by_id(db, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    image_path = BASE_DIR / image.storage_path
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Stored image file not found")

    try:
        result = inspection_pipeline.predict(
            image_path=str(image_path),
            category=inspection_data.category,
            defect_type=inspection_data.defect_type,
        )

        overlay_path = INSPECTION_RESULTS_DIR / f"{image.id}_defect_overlay.png"
        create_defect_overlay(
            image_path=image_path,
            segmentation_mask=result["segmentation_mask"],
            output_path=overlay_path,
        )

        image.category = result["category"]
        image.defect_type = result["defect_type"]
        image.predicted_category = result.get("predicted_category")
        image.predicted_defect_type = result.get("predicted_defect_type")
        image.resolved_defect_status = result.get("resolved_defect_status", result["defect_type"])
        image.classification_confidence = (
            str(result["classification_confidence"])
            if result.get("classification_confidence") is not None
            else None
        )
        image.anomaly_score = str(result["anomaly_score"])
        image.confidence_score = str(result["confidence_score"])
        image.predicted_area_percent = str(result["predicted_area_percent"])
        image.size_score = str(result["size_score"])
        image.location_score = str(result["location_score"])
        image.defect_type_score = str(result["defect_type_score"])
        image.severity_score = str(result["severity_score"])
        image.severity_level = result["severity_level"]
        image.quality_decision = result["quality_decision"]
        image.inspection_status = "completed"

        db.commit()
        db.refresh(image)

        return {
            "image_id": image.id,
            "original_filename": image.original_filename,
            "category": result["category"],
            "defect_type": result["defect_type"],
            "predicted_category": result.get("predicted_category"),
            "predicted_defect_type": result.get("predicted_defect_type"),
            "resolved_defect_status": result.get("resolved_defect_status", result["defect_type"]),
            "inspection_decision": result.get("inspection_decision", "NORMAL" if result["defect_type"] == "normal" else "DEFECTIVE"),
            "classification_confidence": result.get("classification_confidence"),
            "anomaly_score": result["anomaly_score"],
            "confidence_score": result["confidence_score"],
            "predicted_area_percent": result["predicted_area_percent"],
            "size_score": result["size_score"],
            "location_score": result["location_score"],
            "defect_type_score": result["defect_type_score"],
            "severity_score": result["severity_score"],
            "severity_level": result["severity_level"],
            "quality_decision": result["quality_decision"],
            "inspection_overlay_available": overlay_path.exists(),
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Inspection failed: {str(e)}")


@router.get("/")
def get_images(
    current_user=Depends(require_any_role([1, 2])),
    db: Session = Depends(get_db),
):
    images = get_all_images(db)
    return [serialize_image(db, image) for image in images]


@router.get("/supervisor/review-queue")
def get_supervisor_review_queue(
    current_user=Depends(require_role(2)),
    db: Session = Depends(get_db),
):
    images = get_all_images(db)
    return [serialize_image(db, image) for image in images]


@router.get("/{image_id}")
def get_image(
    image_id: int,
    current_user=Depends(require_any_role([1, 2])),
    db: Session = Depends(get_db),
):
    image = get_image_by_id(db, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return serialize_image(db, image)


@router.post("/{image_id}/review")
def review_inspection(
    image_id: int,
    review_data: ImageReviewRequest,
    current_user=Depends(require_role(2)),
    db: Session = Depends(get_db),
):
    image = get_image_by_id(db, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    reviewed_image = review_image(
        db=db,
        image=image,
        decision=review_data.decision,
        notes=review_data.notes,
        reviewed_by=current_user["user_id"],
    )
    return serialize_image(db, reviewed_image)


@router.get("/{image_id}/inspection-overlay")
def get_inspection_overlay(
    image_id: int,
    current_user=Depends(require_any_role([1, 2])),
    db: Session = Depends(get_db),
):
    image = get_image_by_id(db, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    overlay_path = INSPECTION_RESULTS_DIR / f"{image.id}_defect_overlay.png"
    if not overlay_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection overlay not found. Run AI inspection first.",
        )

    return FileResponse(
        path=overlay_path,
        media_type="image/png",
        filename=f"{image.id}_defect_overlay.png",
    )


@router.get("/{image_id}/file")
def get_image_file(
    image_id: int,
    current_user=Depends(require_any_role([1, 2])),
    db: Session = Depends(get_db),
):
    image = get_image_by_id(db, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    file_path = BASE_DIR / image.storage_path
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found")

    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(file_path.suffix.lower())

    if media_type is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format")

    return FileResponse(path=file_path, media_type=media_type, filename=image.original_filename)
