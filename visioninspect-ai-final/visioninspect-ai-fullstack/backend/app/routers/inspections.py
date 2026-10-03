"""
Milestone 2 + 3 - Upload an image, run the CV pipeline, score severity,
store the result, and return it (including the "what can be fixed" column
from the M4 demo feature).
"""
import os, uuid
import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..cv_pipeline import detect_defects, annotate
from ..severity import score_defect, overall_status
from ..fix_suggestions import suggest_fix

router = APIRouter(prefix="/inspections", tags=["inspections"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=schemas.InspectionOut)
async def create_inspection(file: UploadFile = File(...),
                             product_line: Optional[str] = Form(None),
                             batch_id: Optional[str] = Form(None),
                             db: Session = Depends(get_db),
                             user: models.User = Depends(get_current_user)):
    raw = await file.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise HTTPException(400, "Could not decode image. Use JPG, PNG, BMP or WEBP.")
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    raw_defects = detect_defects(gray)
    scored = [score_defect(d, w, h) for d in raw_defects]
    status_ = overall_status(scored)

    annotated = annotate(bgr, scored)
    fname = f"{uuid.uuid4().hex}_{file.filename}"
    annotated_path = os.path.join(UPLOAD_DIR, fname)
    cv2.imwrite(annotated_path, annotated)

    image = models.InspectionImage(
        filename=file.filename, product_line=product_line, batch_id=batch_id,
        width=w, height=h, status=status_, annotated_path=annotated_path, uploaded_by=user.id,
    )
    db.add(image); db.flush()
    for d in scored:
        db.add(models.DefectRecord(
            image_id=image.id, defect_type=d["defect_type"],
            bbox_x=d["bbox_x"], bbox_y=d["bbox_y"], bbox_w=d["bbox_w"], bbox_h=d["bbox_h"],
            area_px=d["area_px"], size_score=d["size_score"], location_score=d["location_score"],
            type_score=d["type_score"], confidence_score=d["confidence_score"],
            severity_score=d["severity_score"], severity_level=d["severity_level"],
            extra={"solidity": d["solidity"], "extent": d["extent"], "aspect": d["aspect"]},
        ))
    db.commit(); db.refresh(image)
    return image


@router.get("", response_model=List[schemas.InspectionOut])
def list_inspections(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.InspectionImage).order_by(models.InspectionImage.uploaded_at.desc()).all()


@router.get("/{inspection_id}", response_model=schemas.InspectionOut)
def get_inspection(inspection_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    image = db.query(models.InspectionImage).get(inspection_id)
    if not image:
        raise HTTPException(404, "Inspection not found")
    return image


@router.get("/{inspection_id}/fixes", response_model=List[schemas.FixSuggestion])
def get_fix_suggestions(inspection_id: int, db: Session = Depends(get_db),
                         user: models.User = Depends(get_current_user)):
    """The 'What Can Be Fixed' column, as its own endpoint."""
    image = db.query(models.InspectionImage).get(inspection_id)
    if not image:
        raise HTTPException(404, "Inspection not found")
    return [suggest_fix(d.defect_type, d.severity_level) for d in image.defects]
