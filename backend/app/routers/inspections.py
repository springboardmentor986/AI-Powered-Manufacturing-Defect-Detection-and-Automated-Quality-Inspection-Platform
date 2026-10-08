import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, UserRole
from ..models.inspection import InspectionRecord, BatchInspection, InspectionStatus, QualityDecision
from ..schemas.inspection import InspectionRecordResponse, BatchInspectionResponse
from ..services.image_service import ImageService
from ..utils.dependencies import get_current_user, require_roles
from ..utils.logger import log_audit_event
from ..config import settings

router = APIRouter(prefix="/inspections", tags=["Inspection Records & Image Acquisition"])

def _build_response_record(rec: InspectionRecord) -> InspectionRecordResponse:
    return InspectionRecordResponse(
        id=rec.id,
        batch_id=rec.batch_id,
        image_filename=rec.image_filename,
        image_url=f"/static/uploads/{rec.image_filename}",
        thumbnail_url=f"/static/thumbnails/thumb_{rec.image_filename.split('.')[0]}.png",
        original_filename=rec.original_filename,
        file_size_bytes=rec.file_size_bytes,
        image_width=rec.image_width,
        image_height=rec.image_height,
        color_channels=rec.color_channels,
        file_format=rec.file_format,
        image_hash=rec.image_hash,
        category=rec.category,
        split=rec.split,
        defect_type=rec.defect_type,
        status=rec.status,
        quality_decision=rec.quality_decision,
        confidence_score=rec.confidence_score,
        severity_score=rec.severity_score,
        severity_level=rec.severity_level,
        inspection_metadata=rec.inspection_metadata or {},
        notes=rec.notes,
        uploaded_by=rec.uploaded_by,
        operator_name=rec.operator.full_name if rec.operator else "Automated System",
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )

@router.post("/upload", response_model=InspectionRecordResponse, status_code=status.HTTP_201_CREATED)
async def upload_single_inspection_image(
    file: UploadFile = File(...),
    category: str = Form("general"),
    split: str = Form("upload"),
    defect_type: str = Form("unclassified"),
    notes: Optional[str] = Form(None),
    batch_id: Optional[str] = Form(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a single manufacturing product image for inspection"""
    processed = await ImageService.process_and_save_upload(
        file=file,
        category=category,
        split=split,
        defect_type=defect_type
    )

    # Initial decision rule (Milestone 1 initialization baseline)
    # If explicitly marked as defect or good, map baseline
    initial_decision = QualityDecision.PENDING
    severity_lvl = None
    if defect_type.lower() == "good":
        initial_decision = QualityDecision.PASS
        severity_lvl = "Low"
    elif defect_type.lower() != "unclassified":
        initial_decision = QualityDecision.FAIL
        severity_lvl = "High"

    record = InspectionRecord(
        id=processed["record_id"],
        batch_id=batch_id,
        image_filename=processed["filename"],
        image_path=processed["image_path"],
        thumbnail_path=processed["thumbnail_path"],
        original_filename=processed["original_filename"],
        file_size_bytes=processed["file_size"],
        image_width=processed["width"],
        image_height=processed["height"],
        color_channels=processed["channels"],
        file_format=processed["format"],
        image_hash=processed["image_hash"],
        category=category,
        split=split,
        defect_type=defect_type,
        status=InspectionStatus.INSPECTED if initial_decision != QualityDecision.PENDING else InspectionStatus.PENDING,
        quality_decision=initial_decision,
        confidence_score=0.96 if initial_decision != QualityDecision.PENDING else None,
        severity_score=15.0 if initial_decision == QualityDecision.PASS else (78.5 if initial_decision == QualityDecision.FAIL else None),
        severity_level=severity_lvl,
        inspection_metadata=processed["metadata"],
        notes=notes,
        uploaded_by=current_user.id,
        created_at=datetime.now(timezone.utc)
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    log_audit_event(
        db,
        action="IMAGE_UPLOAD",
        user=current_user,
        resource_type="inspection",
        resource_id=record.id,
        details={"filename": record.original_filename, "category": category, "size": record.file_size_bytes}
    )

    return _build_response_record(record)

@router.post("/upload-batch", response_model=BatchInspectionResponse)
async def upload_batch_inspection_images(
    files: List[UploadFile] = File(...),
    batch_name: str = Form(...),
    category: str = Form("general"),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Batch upload workflow for bulk industrial inspection"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    batch = BatchInspection(
        batch_name=batch_name,
        description=description,
        category=category,
        total_images=len(files),
        processed_images=0,
        pass_count=0,
        fail_count=0,
        review_count=0,
        status="PROCESSING",
        created_by=current_user.id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    processed_count = 0
    pass_cnt = 0
    fail_cnt = 0

    for f in files:
        try:
            processed = await ImageService.process_and_save_upload(
                file=f,
                category=category,
                split="batch_upload",
                defect_type="unclassified"
            )
            rec = InspectionRecord(
                id=processed["record_id"],
                batch_id=batch.id,
                image_filename=processed["filename"],
                image_path=processed["image_path"],
                thumbnail_path=processed["thumbnail_path"],
                original_filename=processed["original_filename"],
                file_size_bytes=processed["file_size"],
                image_width=processed["width"],
                image_height=processed["height"],
                color_channels=processed["channels"],
                file_format=processed["format"],
                image_hash=processed["image_hash"],
                category=category,
                split="batch_upload",
                defect_type="unclassified",
                status=InspectionStatus.PENDING,
                quality_decision=QualityDecision.PENDING,
                inspection_metadata=processed["metadata"],
                uploaded_by=current_user.id
            )
            db.add(rec)
            processed_count += 1
        except Exception as err:
            continue

    batch.processed_images = processed_count
    batch.status = "COMPLETED"
    db.commit()

    return BatchInspectionResponse(
        id=batch.id,
        batch_name=batch.batch_name,
        description=batch.description,
        category=batch.category,
        total_images=batch.total_images,
        processed_images=batch.processed_images,
        pass_count=batch.pass_count,
        fail_count=batch.fail_count,
        review_count=batch.review_count,
        status=batch.status,
        created_by=batch.created_by,
        creator_name=current_user.full_name,
        created_at=batch.created_at,
        updated_at=batch.updated_at
    )

@router.post("/import-mvtec", response_model=InspectionRecordResponse)
async def import_mvtec_dataset_image(
    category: str = Form(...),
    split: str = Form("test"),
    defect_type: str = Form("good"),
    image_name: str = Form("000.png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import an image from MVTec AD dataset directory into live inspection queue"""
    src_path = settings.MVTEC_DIR / category / split / defect_type / image_name
    if not src_path.exists():
        raise HTTPException(status_code=404, detail=f"Source image not found: {src_path}")

    # Copy to uploads
    import uuid
    new_uuid = str(uuid.uuid4())
    save_filename = f"{new_uuid}.png"
    thumb_filename = f"thumb_{new_uuid}.png"

    dest_img = settings.UPLOADS_DIR / save_filename
    dest_thumb = settings.THUMBNAILS_DIR / thumb_filename
    shutil.copyfile(src_path, dest_img)

    # Make thumbnail & extract meta
    from PIL import Image
    img = Image.open(dest_img)
    thumb = img.copy()
    if thumb.mode in ("RGBA", "P"):
        thumb = thumb.convert("RGB")
    thumb.thumbnail((280, 280), Image.Resampling.LANCZOS)
    thumb.save(dest_thumb, format="PNG")

    meta = ImageService.extract_image_metadata(img)
    img_bytes = dest_img.read_bytes()
    img_hash = ImageService.compute_hash(img_bytes)

    # Initial decision
    is_good = defect_type == "good"
    decision = QualityDecision.PASS if is_good else QualityDecision.FAIL
    sev_score = 12.0 if is_good else 76.4
    sev_level = "Low" if is_good else ("Critical" if "broken" in defect_type or "cut" in defect_type else "High")

    rec = InspectionRecord(
        id=new_uuid,
        image_filename=save_filename,
        image_path=str(dest_img),
        thumbnail_path=str(dest_thumb),
        original_filename=f"{category}_{split}_{defect_type}_{image_name}",
        file_size_bytes=len(img_bytes),
        image_width=meta["width"],
        image_height=meta["height"],
        color_channels=meta["channels"],
        file_format="PNG",
        image_hash=img_hash,
        category=category,
        split=split,
        defect_type=defect_type,
        status=InspectionStatus.INSPECTED,
        quality_decision=decision,
        confidence_score=0.98 if is_good else 0.94,
        severity_score=sev_score,
        severity_level=sev_level,
        inspection_metadata=meta,
        notes=f"Imported from MVTec AD dataset [{category}/{split}/{defect_type}].",
        uploaded_by=current_user.id
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)

    return _build_response_record(rec)

@router.get("", response_model=List[InspectionRecordResponse])
def get_inspections(
    category: Optional[str] = None,
    status: Optional[str] = None,
    decision: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve inspection records with multi-criteria filtering"""
    query = db.query(InspectionRecord)

    if category and category != "all":
        query = query.filter(InspectionRecord.category == category)
    if status and status != "all":
        query = query.filter(InspectionRecord.status == status)
    if decision and decision != "all":
        query = query.filter(InspectionRecord.quality_decision == decision)
    if search:
        query = query.filter(
            (InspectionRecord.original_filename.ilike(f"%{search}%")) |
            (InspectionRecord.defect_type.ilike(f"%{search}%")) |
            (InspectionRecord.category.ilike(f"%{search}%"))
        )

    records = query.order_by(InspectionRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [_build_response_record(r) for r in records]

@router.get("/{record_id}", response_model=InspectionRecordResponse)
def get_inspection_detail(record_id: str, db: Session = Depends(get_db)):
    """Get single inspection details and technical metrics"""
    rec = db.query(InspectionRecord).filter(InspectionRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Inspection record not found.")
    return _build_response_record(rec)

@router.post("/{record_id}/decision", response_model=InspectionRecordResponse)
def update_inspection_decision(
    record_id: str,
    decision: str = Form(...),
    severity_level: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(require_roles([UserRole.QUALITY_ENGINEER, UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER])),
    db: Session = Depends(get_db)
):
    """Quality Engineer / Supervisor decision override and sign-off"""
    rec = db.query(InspectionRecord).filter(InspectionRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    rec.quality_decision = decision.upper()
    rec.status = InspectionStatus.INSPECTED
    if severity_level:
        rec.severity_level = severity_level
    if notes:
        rec.notes = notes
    rec.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rec)

    log_audit_event(
        db,
        action="DECISION_OVERRIDE",
        user=current_user,
        resource_type="inspection",
        resource_id=rec.id,
        details={"new_decision": rec.quality_decision, "severity": rec.severity_level}
    )

    return _build_response_record(rec)

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inspection(
    record_id: str,
    current_user: User = Depends(require_roles([UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete inspection record (Supervisor/Manager permission only)"""
    rec = db.query(InspectionRecord).filter(InspectionRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    # Remove files
    try:
        if Path(rec.image_path).exists():
            Path(rec.image_path).unlink()
        if rec.thumbnail_path and Path(rec.thumbnail_path).exists():
            Path(rec.thumbnail_path).unlink()
    except Exception:
        pass

    db.delete(rec)
    db.commit()

    log_audit_event(
        db,
        action="INSPECTION_DELETED",
        user=current_user,
        resource_type="inspection",
        resource_id=record_id
    )
