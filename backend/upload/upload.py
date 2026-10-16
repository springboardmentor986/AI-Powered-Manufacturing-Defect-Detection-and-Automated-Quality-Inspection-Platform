from fastapi import APIRouter, UploadFile, File, Form

from backend.preprocess import (
    preprocess_image,
    analyze_image_quality
)

from backend.feature_extractor import extract_features
from backend.anomaly_detector import predict_anomaly
from backend.defect_classifier import predict_defect

from backend.confidence import calculate_confidence
from backend.defect_scoring import get_defect_type_score
from backend.defect_size import get_defect_size_score
from backend.defect_location import get_defect_location_score
from backend.severity_scoring import calculate_severity
from backend.risk_assessment import assess_quality_risk
from backend.quality_report import generate_quality_report

from backend.inspection_history import add_inspection

import torch
from datetime import datetime
import uuid


router = APIRouter()


# ==========================================
# Load Normal Feature Database
# ==========================================

normal_features = torch.load(
    "normal_features.pt",
    weights_only=False
)


# ==========================================
# MVTec AD Categories
# ==========================================

CATEGORIES = [
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
    "zipper"
]


# ==========================================
# Category-Specific Thresholds
# ==========================================

THRESHOLDS = {
    "bottle": 1.1508,
    "cable": 1.8222,
    "capsule": 0.9139,
    "carpet": 0.6511,
    "grid": 1.0459,
    "hazelnut": 2.3201,
    "leather": 0.7306,
    "metal_nut": 1.8214,
    "pill": 1.0704,
    "screw": 1.6943,
    "tile": 1.2502,
    "toothbrush": 1.6475,
    "transistor": 1.7346,
    "wood": 1.3598,
    "zipper": 1.4081
}


# ==========================================
# Inspection Endpoint
# ==========================================

@router.post("/upload")
async def upload_image(
    category: str = Form(...),
    file: UploadFile = File(...)
):

    # ======================================
    # Validate Category
    # ======================================

    if category not in CATEGORIES:
        return {
            "message": "Invalid category",
            "available_categories": CATEGORIES
        }


    # ======================================
    # Get Category Normal Features
    # ======================================

    category_features = normal_features.get(
        category
    )

    if category_features is None:
        return {
            "message": (
                "Normal features not found "
                "for this category"
            ),
            "category": category
        }


    # ======================================
    # Get Category Threshold
    # ======================================

    threshold = THRESHOLDS.get(
        category
    )

    if threshold is None:
        return {
            "message": (
                "Threshold not configured "
                "for this category"
            ),
            "category": category
        }


    # ======================================
    # Read Image
    # ======================================

    image_bytes = await file.read()


    # ======================================
    # Image Quality Analysis
    # ======================================

    quality_report = analyze_image_quality(
        image_bytes
    )


    # ======================================
    # Image Preprocessing
    # ======================================

    image = preprocess_image(
        image_bytes
    )


    # ======================================
    # Feature Extraction
    # ======================================

    features = extract_features(
        image
    )


    # ======================================
    # Anomaly Detection
    # ======================================

    result = predict_anomaly(
        features,
        category_features,
        threshold=threshold
    )


    # ======================================
    # Defect Categorization
    # ======================================

    defect_type = None

    if (
        category == "bottle"
        and result["result"] == "DEFECT"
    ):
        defect_type = predict_defect(
            features
        )


    # ======================================
    # Severity + Risk Assessment
    # ======================================

    severity_report = None
    risk_report = None

    if result["result"] == "DEFECT":

        # Confidence
        confidence_score = calculate_confidence(
            result["anomaly_score"],
            threshold
        )

        # Defect type
        defect_type_score = get_defect_type_score(
            defect_type
        )

        # Defect size
        defect_size_score = get_defect_size_score(
            defect_type
        )

        # Defect location
        defect_location_score = (
            get_defect_location_score(
                defect_type
            )
        )

        # Calculate severity
        severity_report = calculate_severity(
            defect_size_score,
            defect_location_score,
            defect_type_score,
            confidence_score
        )

        # Store individual scores
        severity_report[
            "defect_size_score"
        ] = defect_size_score

        severity_report[
            "location_score"
        ] = defect_location_score

        severity_report[
            "defect_type_score"
        ] = defect_type_score

        severity_report[
            "confidence_score"
        ] = confidence_score

        # Quality risk
        risk_report = assess_quality_risk(
            severity_report["severity_score"],
            severity_report["severity_level"]
        )


    # ======================================
    # Generate Inspection ID
    # ======================================

    inspection_id = (
        "INS-"
        + uuid.uuid4().hex[:8].upper()
    )


    # ======================================
    # Inspection Timestamp
    # ======================================

    inspection_time = (
        datetime.now().isoformat()
    )


    # ======================================
    # Determine Product Status
    # ======================================

    if result["result"] == "DEFECT":
        product_status = "REJECT"
    else:
        product_status = "ACCEPT"


    # ======================================
    # Generate Production Quality Report
    # ======================================

    production_quality_report = (
        generate_quality_report(
            inspection_id=inspection_id,
            category=category,
            prediction=result["result"],
            defect_type=defect_type,
            severity_report=severity_report,
            risk_report=risk_report,
            product_status=product_status
        )
    )


    # ======================================
    # Build Inspection Report
    # ======================================

    inspection_report = {

        "inspection_id": inspection_id,

        "inspection_time": inspection_time,

        "filename": file.filename,

        "category": category,

        "prediction": result["result"],

        "defect_type": defect_type,

        "severity_report": severity_report,

        "risk_report": risk_report,

        "production_quality_report": (
            production_quality_report
        ),

        "product_status": product_status,

        "anomaly_score": result[
            "anomaly_score"
        ],

        "threshold": result[
            "threshold"
        ],

        "decision": result[
            "decision"
        ],

        "image_shape": list(
            image.shape
        ),

        "feature_shape": list(
            features.shape
        ),

        "quality_report": quality_report
    }


    # ======================================
    # Store Inspection
    # ======================================

    add_inspection(
        inspection_report
    )


    # ======================================
    # Final API Response
    # ======================================

    return {

        "message": (
            "Inspection completed successfully"
        ),

        "inspection_report": (
            inspection_report
        )
    }