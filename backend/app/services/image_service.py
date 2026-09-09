from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image as PILImage, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.models.image import Image


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_file_type(content_type: str | None):
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            "Only JPEG and PNG images are allowed"
        )

async def validate_file_size(file: UploadFile):
    total_size = 0
    while chunk := await file.read(1024 * 1024):
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise ValueError("File size must not exceed 5 MB")
    await file.seek(0)

def validate_image_content(file: UploadFile):
    try:
        file.file.seek(0)
        with PILImage.open(file.file) as image:
            image.verify()
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("Only JPEG and PNG images are allowed")
    except (UnidentifiedImageError, OSError):
        raise ValueError("Uploaded file is not a valid image")
    finally:
        file.file.seek(0)

def generate_stored_filename(user_id: int, original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_id = uuid4().hex[:8]
    return (
        f"{user_id}_"
        f"{timestamp}_"
        f"{unique_id}"
        f"{extension}"
    )

async def save_image(file: UploadFile, stored_filename: str) -> str:
    UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
    file_path = UPLOAD_DIR / stored_filename
    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)
    await file.seek(0)
    return str(file_path.relative_to(BASE_DIR))

def create_image_record(
    db: Session,
    original_filename: str,
    stored_filename: str,
    storage_path: str,
    uploaded_by: int,
):
    image = Image(
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=storage_path,
        uploaded_by=uploaded_by,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image

def get_all_images(db: Session):
    return db.query(Image).order_by(Image.uploaded_at.desc()).all()

def get_image_by_id(db: Session, image_id: int):
    return db.query(Image).filter(Image.id == image_id).first()


def review_image(
    db: Session,
    image: Image,
    decision: str,
    notes: str | None,
    reviewed_by: int,
):
    image.inspection_status = "reviewed"
    image.supervisor_decision = decision
    image.supervisor_notes = notes
    image.reviewed_by = reviewed_by
    image.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(image)

    return image
