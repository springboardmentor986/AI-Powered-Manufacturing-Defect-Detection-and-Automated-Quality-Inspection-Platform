import os
import uuid

import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models, auth
from ..database import get_db

router = APIRouter(prefix="/images", tags=["Images"])

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tif", "tiff", "webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_IMAGE_SIDE = 32  # pixels


@router.post("/upload")
def upload_image(
    category_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # 1. File type
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a JPG, PNG, BMP, TIFF or WebP image.",
        )

    # 2. Category must exist
    category = (
        db.query(models.Category)
        .filter(models.Category.category_id == category_id)
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=404, detail=f"Category {category_id} does not exist."
        )

    # 3. Size
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400, detail="File is too large. Maximum size is 10 MB."
        )

    # 4. Must really decode as an image
    decoded = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=400, detail="The file is not a valid image.")
    height, width = decoded.shape[:2]
    if min(height, width) < MIN_IMAGE_SIDE:
        raise HTTPException(
            status_code=400,
            detail=f"Image is too small. Minimum side is {MIN_IMAGE_SIDE} pixels.",
        )

    unique_name = f"{uuid.uuid4()}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(save_path, "wb") as buffer:
        buffer.write(data)

    new_image = models.Image(
        category_id=category_id,
        uploaded_by=current_user.user_id,
        image_path=save_path,
        image_source="uploaded",
        image_type="uploaded",
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return {
        "image_id": new_image.image_id,
        "image_path": new_image.image_path,
        "message": "Image uploaded successfully",
    }


@router.post("/upload")
def upload_image(
    category_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_image = models.Image(
        category_id=category_id,
        uploaded_by=current_user.user_id,
        image_path=save_path,
        image_source="uploaded",
        image_type="uploaded",
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return {
        "image_id": new_image.image_id,
        "image_path": new_image.image_path,
        "message": "Image uploaded successfully",
    }


@router.get("/")
def list_images(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Lists all images, each annotated with its latest inspection status
    (None if the unit hasn't been inspected yet) — used by the dashboard
    to show a Pass/Fail/Pending badge without a separate request per unit.
    """
    images = db.query(models.Image).all()
    inspections = db.query(models.Inspection).all()

    latest_by_image = {}
    for insp in inspections:
        existing = latest_by_image.get(insp.image_id)
        if not existing or insp.inspection_time > existing.inspection_time:
            latest_by_image[insp.image_id] = insp

    result = []
    for img in images:
        insp = latest_by_image.get(img.image_id)
        result.append(
            {
                "image_id": img.image_id,
                "category_id": img.category_id,
                "uploaded_by": img.uploaded_by,
                "image_path": img.image_path,
                "image_source": img.image_source,
                "image_type": img.image_type,
                "created_at": img.created_at,
                "inspection_status": insp.result if insp else None,
            }
        )
    return result


@router.get("/{image_id}")
def get_image_detail(
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

    inspection = (
        db.query(models.Inspection)
        .filter(models.Inspection.image_id == image_id)
        .order_by(models.Inspection.inspection_time.desc())
        .first()
    )

    defects = []
    if inspection:
        defects = (
            db.query(models.Defect)
            .filter(models.Defect.inspection_id == inspection.inspection_id)
            .all()
        )

    return {
        "image_id": image.image_id,
        "image_path": image.image_path,
        "image_source": image.image_source,
        "image_type": image.image_type,
        "category": category.category_name if category else None,
        "created_at": image.created_at,
        "inspection": inspection,
        "defects": defects,
    }


@router.get("/{image_id}/file")
def get_image_file(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = db.query(models.Image).filter(models.Image.image_id == image_id).first()
    if not image or not os.path.exists(image.image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(image.image_path)
