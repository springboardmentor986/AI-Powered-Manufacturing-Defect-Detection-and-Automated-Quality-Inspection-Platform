import hashlib
import io
import uuid
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageStat
import numpy as np
from fastapi import UploadFile, HTTPException, status
from ..config import settings

class ImageService:
    @staticmethod
    def validate_file(file: UploadFile) -> str:
        """Validate filename extension and mime type"""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File has no name."
            )
        
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return ext

    @staticmethod
    def compute_hash(file_bytes: bytes) -> str:
        """Compute SHA-256 hash of file bytes"""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def extract_image_metadata(img: Image.Image) -> Dict[str, Any]:
        """Extract dimension, color channels, format, and image quality metrics"""
        width, height = img.size
        mode = img.mode
        channels = len(img.getbands())
        img_format = img.format or "PNG"

        # Image stats (brightness, contrast)
        stat = ImageStat.Stat(img)
        mean_brightness = float(np.mean(stat.mean)) if stat.mean else 0.0
        contrast_std = float(np.mean(stat.stddev)) if stat.stddev else 0.0

        # Rough Sharpness estimation using pixel variance
        gray = img.convert("L")
        gray_arr = np.array(gray, dtype=np.float32)
        gy, gx = np.gradient(gray_arr)
        sharpness_score = float(np.mean(gx**2 + gy**2))

        return {
            "width": width,
            "height": height,
            "mode": mode,
            "channels": channels,
            "format": img_format,
            "mean_brightness": round(mean_brightness, 2),
            "contrast_std": round(contrast_std, 2),
            "sharpness_score": round(sharpness_score, 2),
            "aspect_ratio": round(width / max(height, 1), 3),
        }

    @classmethod
    async def process_and_save_upload(
        cls,
        file: UploadFile,
        category: str = "general",
        split: str = "upload",
        defect_type: str = "unclassified"
    ) -> Dict[str, Any]:
        """
        Validates, saves full resolution image, generates thumbnail,
        and computes technical image metrics.
        """
        ext = cls.validate_file(file)
        contents = await file.read()

        # Check file size limit
        file_size = len(contents)
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum limit of {settings.MAX_FILE_SIZE_MB}MB."
            )

        # Validate with PIL
        try:
            img = Image.open(io.BytesIO(contents))
            img.verify() # Verify file integrity
            # Reopen after verify
            img = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupted or invalid image file: {str(e)}"
            )

        # Unique file naming
        file_uuid = str(uuid.uuid4())
        save_filename = f"{file_uuid}{ext}"
        thumb_filename = f"thumb_{file_uuid}.png"

        save_path = settings.UPLOADS_DIR / save_filename
        thumb_path = settings.THUMBNAILS_DIR / thumb_filename

        # Save original file
        with open(save_path, "wb") as f:
            f.write(contents)

        # Generate & save thumbnail (RGB mode)
        thumb_img = img.copy()
        if thumb_img.mode in ("RGBA", "P"):
            thumb_img = thumb_img.convert("RGB")
        thumb_img.thumbnail((280, 280), Image.Resampling.LANCZOS)
        thumb_img.save(thumb_path, format="PNG", optimize=True)

        # Metadata
        img_meta = cls.extract_image_metadata(img)
        img_hash = cls.compute_hash(contents)

        return {
            "record_id": file_uuid,
            "filename": save_filename,
            "original_filename": file.filename,
            "image_path": str(save_path),
            "thumbnail_path": str(thumb_path),
            "relative_image_url": f"/static/uploads/{save_filename}",
            "relative_thumbnail_url": f"/static/thumbnails/{thumb_filename}",
            "file_size": file_size,
            "width": img_meta["width"],
            "height": img_meta["height"],
            "channels": img_meta["channels"],
            "format": ext.replace(".", "").upper(),
            "image_hash": img_hash,
            "metadata": img_meta,
            "category": category,
            "split": split,
            "defect_type": defect_type
        }
