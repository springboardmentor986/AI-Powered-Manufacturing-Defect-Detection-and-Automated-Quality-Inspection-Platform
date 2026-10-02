import os
import sys
import uuid
import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    Query,
)

from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.connection import get_db
from models.inspection import Inspection


# ============================================================
# ML PIPELINE IMPORT
# ============================================================

# Path to D:\VisionInspectAI\ml
ML_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "ml"
    )
)

if ML_DIR not in sys.path:
    sys.path.append(ML_DIR)


try:

    from inference.inspection_pipeline import (
        inspect_image
    )

except Exception as error:

    print(
        f"ML pipeline import error: {error}"
    )

    inspect_image = None


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/inspections",
    tags=["Inspections"]
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

UPLOAD_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "uploads"
    )
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

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


def validate_category(category: str) -> str:
    normalized = category.lower().strip()
    if normalized not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Available categories: "
            f"{sorted(ALLOWED_CATEGORIES)}",
        )
    return normalized


async def run_uploaded_inspection(file: UploadFile, category: str, current_user: dict, db: Session):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG and WEBP images are allowed",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    extension = os.path.splitext(file.filename or "")[1].lower()
    stored_filename = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    inspection = Inspection(
        filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        user_id=int(current_user["user_id"]),
        role=current_user["role"],
        status="processing",
        result=json.dumps({"category": category, "status": "PROCESSING"}),
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    if inspect_image is None:
        raise HTTPException(status_code=500, detail="ML inspection pipeline is unavailable")

    try:
        ml_result = inspect_image(file_path, category)
        inspection.status = "completed"
        inspection.result = json.dumps(ml_result)
        db.commit()
        db.refresh(inspection)
    except Exception as error:
        inspection.status = "failed"
        inspection.result = json.dumps({"error": str(error)})
        db.commit()
        raise HTTPException(status_code=500, detail=f"ML inspection failed: {error}") from error

    return {
        "inspection_id": str(inspection.id),
        "filename": inspection.filename,
        "category": category,
        "status": inspection.status,
        "result": ml_result,
    }


# ============================================================
# UPLOAD + ML INSPECTION
# ============================================================

@router.post("/upload")
async def upload_inspection_image(

    file: UploadFile = File(...),

    category: str = "bottle",

    current_user: dict = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )
):

    # --------------------------------------------------------
    # Validate image type
    # --------------------------------------------------------

    if file.content_type not in ALLOWED_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPEG, PNG and WEBP "
                "images are allowed"
            )
        )


    # --------------------------------------------------------
    # Validate category
    # --------------------------------------------------------

    category = validate_category(category)


    # --------------------------------------------------------
    # Generate unique filename
    # --------------------------------------------------------

    extension = os.path.splitext(
        file.filename
    )[1].lower()


    stored_filename = (
        f"{uuid.uuid4()}{extension}"
    )


    file_path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )


    # --------------------------------------------------------
    # Read uploaded image
    # --------------------------------------------------------

    contents = await file.read()


    if len(contents) == 0:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )


    # --------------------------------------------------------
    # Save image
    # --------------------------------------------------------

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(
            contents
        )


    # --------------------------------------------------------
    # Create inspection record
    # --------------------------------------------------------

    inspection = Inspection(

        filename=file.filename,

        stored_filename=stored_filename,

        user_id=int(
            current_user["user_id"]
        ),

        role=current_user["role"],

        status="processing",

        result=json.dumps({"category": category, "status": "PROCESSING"})
    )


    db.add(
        inspection
    )

    db.commit()

    db.refresh(
        inspection
    )


    # ========================================================
    # RUN ML PIPELINE
    # ========================================================

    if inspect_image is None:

        inspection.status = "failed"

        inspection.result = json.dumps({

            "error":
                "ML inspection pipeline "
                "could not be imported"
        })

        db.commit()

        raise HTTPException(

            status_code=500,

            detail=(
                "ML inspection pipeline "
                "is unavailable"
            )
        )


    try:

        # ----------------------------------------------------
        # Autoencoder → YOLO → ResNet18
        # → Severity → PASS/FAIL
        # ----------------------------------------------------

        ml_result = inspect_image(

            file_path,

            category
        )


        # ----------------------------------------------------
        # Save ML result
        # ----------------------------------------------------

        inspection.status = (
            "completed"
        )

        inspection.result = json.dumps(
            ml_result
        )

        db.commit()

        db.refresh(
            inspection
        )


    except Exception as error:

        inspection.status = (
            "failed"
        )

        inspection.result = json.dumps({

            "error": str(error)

        })

        db.commit()

        raise HTTPException(

            status_code=500,

            detail=(
                f"ML inspection failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "message":
            "Inspection completed successfully",

        "inspection_id":
            str(inspection.id),

        "filename":
            inspection.filename,

        "category":
            category,

        "status":
            inspection.status,

        "result":
            ml_result
    }


@router.post("/batch-upload")
async def upload_batch(
    files: list[UploadFile] = File(...),
    category: str = Query("bottle"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = validate_category(category)
    if not files:
        raise HTTPException(status_code=400, detail="Select at least one image")
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Batch limit is 50 images")

    results = []
    for file in files:
        try:
            results.append(
                await run_uploaded_inspection(file, category, current_user, db)
            )
        except HTTPException as error:
            results.append({
                "filename": file.filename or "unknown",
                "category": category,
                "status": "failed",
                "error": error.detail,
            })

    return {
        "category": category,
        "total": len(results),
        "completed": sum(item["status"] == "completed" for item in results),
        "failed": sum(item["status"] == "failed" for item in results),
        "results": results,
    }


@router.delete("/{inspection_id}")
def delete_inspection(
    inspection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inspection = (
        db.query(Inspection)
        .filter(
            Inspection.id == inspection_id,
            Inspection.user_id == int(current_user["user_id"]),
        )
        .first()
    )

    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")

    stored_path = os.path.join(UPLOAD_DIR, inspection.stored_filename)
    if os.path.exists(stored_path):
        os.remove(stored_path)

    db.delete(inspection)
    db.commit()
    return {"message": "Inspection deleted", "inspection_id": str(inspection_id)}


@router.post("/{inspection_id}/retry")
def retry_inspection(
    inspection_id: int,
    category: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inspection = (
        db.query(Inspection)
        .filter(
            Inspection.id == inspection_id,
            Inspection.user_id == int(current_user["user_id"]),
        )
        .first()
    )
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")

    if not category and inspection.result:
        try:
            category = json.loads(inspection.result).get("category")
        except (TypeError, ValueError):
            category = None
    category = validate_category(category or "bottle")

    file_path = os.path.join(UPLOAD_DIR, inspection.stored_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original inspection image is unavailable")
    if inspect_image is None:
        raise HTTPException(status_code=500, detail="ML inspection pipeline is unavailable")

    try:
        inspection.status = "processing"
        db.commit()
        ml_result = inspect_image(file_path, category)
        inspection.status = "completed"
        inspection.result = json.dumps(ml_result)
        db.commit()
        db.refresh(inspection)
        return {
            "inspection_id": str(inspection.id),
            "filename": inspection.filename,
            "category": category,
            "status": inspection.status,
            "result": ml_result,
        }
    except Exception as error:
        inspection.status = "failed"
        inspection.result = json.dumps({"error": str(error), "category": category})
        db.commit()
        raise HTTPException(status_code=500, detail=f"Inspection retry failed: {error}") from error


# ============================================================
# GET INSPECTION HISTORY
# ============================================================

# ============================================================
# GET INSPECTION HISTORY
# ============================================================

@router.get("/")
def get_inspections(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = int(current_user["user_id"])
    user_role = current_user.get("role")

    query = db.query(Inspection)

    # Quality Engineer → only their own inspections
    if user_role == "quality_engineer":
        query = query.filter(
            Inspection.user_id == user_id
        )

    # Factory Supervisor → all inspections
    elif user_role == "factory_supervisor":
        pass

    inspections = (
        query
        .order_by(
            Inspection.created_at.desc()
        )
        .all()
    )

    results = []

    for inspection in inspections:

        parsed_result = None

        if inspection.result:

            try:
                parsed_result = json.loads(
                    inspection.result
                )

            except Exception:
                parsed_result = inspection.result

        results.append({

            "id":
                str(inspection.id),

            "filename":
                inspection.filename,

            "stored_filename":
                inspection.stored_filename,

            "user_id":
                inspection.user_id,

            "role":
                inspection.role,

            "status":
                inspection.status,

            "result":
                parsed_result,

            "created_at":
                inspection.created_at
        })

    return results