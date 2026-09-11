from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import os
import shutil
import uuid
import cv2
from datetime import datetime
from app.database import inspections_collection, products_collection
from app.preprocessing import advanced_preprocess_image
from app.quality_analysis import analyze_image_quality
from app.ai_model import detect_defects, draw_defect_result, MODEL_INFO
from bson import ObjectId

router = APIRouter(prefix="/inspections", tags=["Inspections"])

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
RESULTS_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def validate_image(file_path: str):
    try:
        img = cv2.imread(file_path)
        if img is None:
            return False, "Could not read image file"
        height, width = img.shape[:2]
        if height < 10 or width < 10:
            return False, "Image dimensions too small"
        if height > 10000 or width > 10000:
            return False, "Image dimensions too large"
        return True, "Image valid"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


@router.post("/upload")
async def upload_and_inspect(
    product_id: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        file_ext = os.path.splitext(image.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, "File type not allowed")
        
        product = None
        try:
            if ObjectId.is_valid(product_id):
                product = products_collection.find_one({"_id": ObjectId(product_id)})
        except:
            pass
        
        if not product:
            product = products_collection.find_one({"product_code": product_id})
        
        if not product:
            product = products_collection.find_one({})
        
        if not product:
            raise HTTPException(404, "No products found")
        
        unique_filename = f"{uuid.uuid4()}_{image.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        is_valid, message = validate_image(file_path)
        if not is_valid:
            os.remove(file_path)
            raise HTTPException(400, message)
        
        quality_analysis = analyze_image_quality(file_path)
        processed_info = advanced_preprocess_image(file_path, PROCESSED_DIR)
        detection_result = detect_defects(file_path, product.get("product_code", ""))
        
        result_image_filename = f"result_{uuid.uuid4().hex[:8]}.jpg"
        result_image_path = os.path.join(RESULTS_DIR, result_image_filename)
        
        if detection_result.get("defect_detected"):
            primary_defect = {
                "type": detection_result["defect_type"],
                "confidence": detection_result["confidence"],
                "location": detection_result["location"]
            }
            draw_defect_result(
                file_path, 
                primary_defect, 
                result_image_path,
                detection_result["severity_level"]
            )
        else:
            shutil.copy(file_path, result_image_path)
        
        inspection_data = {
            "product_id": str(product["_id"]),
            "product_name": product.get("product_name", "Unknown"),
            "product_code": product.get("product_code", "Unknown"),
            "image_path": file_path,
            "processed_image_path": processed_info["processed_path"],
            "result_image_path": result_image_path,
            "image_filename": image.filename,
            "status": "completed",
            "image_width": processed_info["original_width"],
            "image_height": processed_info["original_height"],
            "file_size": processed_info["file_size"],
            "quality_analysis": quality_analysis,
            "preprocessing_steps": processed_info["steps"],
            "defect_detected": detection_result.get("defect_detected", False),
            "defect_type": detection_result.get("defect_type"),
            "confidence": detection_result.get("confidence", 0),
            "defect_location": detection_result.get("location"),
            "all_defects": detection_result.get("all_defects", []),
            "severity_score": detection_result.get("severity_score", 0),
            "severity_level": detection_result.get("severity_level", "None"),
            "decision": detection_result.get("decision", "PASSED"),
            "recommendation": detection_result.get("recommendation", ""),
            "timing": detection_result.get("timing", {}),
            "model_info": detection_result.get("model_info", MODEL_INFO),
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow()
        }
        
        result = inspections_collection.insert_one(inspection_data)
        inspection_data["id"] = str(result.inserted_id)
        
        return {
            "message": "✅ Inspection completed",
            "inspection": {
                "id": inspection_data["id"],
                "product_name": inspection_data["product_name"],
                "product_code": inspection_data["product_code"],
                "image_filename": inspection_data["image_filename"],
                "status": inspection_data["status"],
                "created_at": inspection_data["created_at"].isoformat()
            },
            "validation": {"status": "passed", "message": message},
            "preprocessing": {
                "original_size": f"{processed_info['original_width']}x{processed_info['original_height']}",
                "processed_size": "224x224",
                "steps": processed_info["steps"]
            },
            "quality_analysis": quality_analysis,
            "ai_detection": {
                "defect_detected": detection_result.get("defect_detected"),
                "defect_type": detection_result.get("defect_type"),
                "confidence": detection_result.get("confidence"),
                "location": detection_result.get("location"),
                "all_defects": detection_result.get("all_defects", []),
                "severity_score": detection_result.get("severity_score"),
                "severity_level": detection_result.get("severity_level"),
                "decision": detection_result.get("decision"),
                "recommendation": detection_result.get("recommendation"),
                "timing": detection_result.get("timing", {}),
                "model_info": detection_result.get("model_info", {})
            },
            "result_image_url": f"http://127.0.0.1:8000/results/{result_image_filename}",
            "processed_image_url": f"http://127.0.0.1:8000/processed/{os.path.basename(processed_info['processed_path'])}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Inspection error: {str(e)}")


@router.get("/")
def get_inspections():
    inspections = list(inspections_collection.find().sort("created_at", -1))
    for inspection in inspections:
        inspection["id"] = str(inspection["_id"])
        inspection.pop("_id", None)
    return inspections


@router.get("/stats")
def get_stats():
    total = inspections_collection.count_documents({})
    defective = inspections_collection.count_documents({"defect_detected": True})
    passed = inspections_collection.count_documents({"decision": "PASSED"})
    failed = inspections_collection.count_documents({"decision": "FAILED"})
    critical = inspections_collection.count_documents({"severity_level": "Critical"})
    high = inspections_collection.count_documents({"severity_level": "High"})
    medium = inspections_collection.count_documents({"severity_level": "Medium"})
    low = inspections_collection.count_documents({"severity_level": "Low"})
    
    defect_rate = (defective / total * 100) if total > 0 else 0
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "defective": defective,
        "passed": passed,
        "failed": failed,
        "defect_rate": round(defect_rate, 2),
        "pass_rate": round(pass_rate, 2),
        "by_severity": {
            "Critical": critical,
            "High": high,
            "Medium": medium,
            "Low": low
        }
    }


@router.get("/{inspection_id}")
def get_inspection(inspection_id: str):
    try:
        inspection = inspections_collection.find_one({"_id": ObjectId(inspection_id)})
    except:
        inspection = inspections_collection.find_one({"_id": inspection_id})
    
    if not inspection:
        raise HTTPException(404, "Inspection not found")
    
    inspection["id"] = str(inspection["_id"])
    inspection.pop("_id", None)
    return inspection
