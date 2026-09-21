import os
import uuid
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session

from app.config import settings
from app.cv_pipeline import detect_defects, overall_status
from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import DefectRecord, InspectionImage, InspectionStatus, User, UserRole
from app.schemas import InspectionImageOut

router = APIRouter(prefix="/api/images", tags=["images"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def _validate_upload(file: UploadFile, raw_bytes: bytes):
    """Image validation, per the Image Acquisition Module."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 15MB limit")


def _process_and_store(
    db: Session,
    raw_bytes: bytes,
    filename: str,
    product_line: Optional[str],
    batch_id: Optional[str],
    user: User,
) -> InspectionImage:
    npimg = np.frombuffer(raw_bytes, np.uint8)
    image_bgr = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="File could not be decoded as an image")

    unique_id = uuid.uuid4().hex[:12]
    ext = os.path.splitext(filename)[1].lower() or ".png"
    raw_name = f"{unique_id}{ext}"
    annotated_name = f"{unique_id}_annotated.png"

    raw_path = os.path.join(settings.upload_dir, "raw", raw_name)
    annotated_path = os.path.join(settings.upload_dir, "annotated", annotated_name)

    with open(raw_path, "wb") as f:
        f.write(raw_bytes)

    defects, annotated_img = detect_defects(image_bgr)
    cv2.imwrite(annotated_path, annotated_img)

    status_str = overall_status(defects)
    status_enum = {
        "pass": InspectionStatus.pass_,
        "fail": InspectionStatus.fail,
        "review": InspectionStatus.review,
    }[status_str]

    h, w = image_bgr.shape[:2]
    record = InspectionImage(
        filename=filename,
        stored_path=raw_path,
        annotated_path=annotated_path,
        product_line=product_line,
        batch_id=batch_id,
        uploaded_by_id=user.id,
        width=w,
        height=h,
        status=status_enum,
        processed=True,
    )
    db.add(record)
    db.flush()  # get record.id before adding children

    for d in defects:
        db.add(DefectRecord(
            image_id=record.id,
            defect_type=d.defect_type,
            bbox_x=d.bbox[0], bbox_y=d.bbox[1], bbox_w=d.bbox[2], bbox_h=d.bbox[3],
            area_px=d.area_px,
            size_score=d.size_score,
            location_score=d.location_score,
            type_score=d.type_score,
            confidence_score=d.confidence_score,
            severity_score=d.severity_score,
            severity_level=d.severity_level,
        ))

    db.commit()
    db.refresh(record)
    return record


@router.post("/upload", response_model=InspectionImageOut, status_code=201)
def upload_image(
    file: UploadFile = File(...),
    product_line: Optional[str] = Form(None),
    batch_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Image Acquisition Module: single product image upload.
    Runs synchronously through the full detection pipeline and returns
    the inspection result immediately.
    """
    raw_bytes = file.file.read()
    _validate_upload(file, raw_bytes)
    record = _process_and_store(db, raw_bytes, file.filename, product_line, batch_id, current_user)
    return record


@router.post("/upload-batch", response_model=List[InspectionImageOut], status_code=201)
def upload_batch(
    files: List[UploadFile] = File(...),
    product_line: Optional[str] = Form(None),
    batch_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch image processing, per the Image Acquisition Module."""
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Batch limit is 50 images per request")

    results = []
    for file in files:
        raw_bytes = file.file.read()
        _validate_upload(file, raw_bytes)
        record = _process_and_store(db, raw_bytes, file.filename, product_line, batch_id, current_user)
        results.append(record)
    return results


@router.get("/{image_id}/annotated")
def get_annotated_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi.responses import FileResponse
    record = db.query(InspectionImage).filter(InspectionImage.id == image_id).first()
    if not record or not record.annotated_path or not os.path.exists(record.annotated_path):
        raise HTTPException(status_code=404, detail="Annotated image not found")
    return FileResponse(record.annotated_path, media_type="image/png")
