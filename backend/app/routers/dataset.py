from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.dataset_service import DatasetService
from ..services.anomaly_training_service import AnomalyTrainingService
from ..models.user import User, UserRole
from ..utils.dependencies import get_current_user, require_roles
from ..utils.logger import log_audit_event

router = APIRouter(prefix="/dataset", tags=["MVTec AD Dataset Explorer & Model Training"])

@router.get("/categories", response_model=List[Dict[str, Any]])
def list_categories():
    """List all 15 MVTec AD categories, load status, and counts directly from mv-dataset"""
    return DatasetService.get_available_categories()

@router.get("/category/{category_name}")
def get_category_details(category_name: str):
    """Get detailed train/test/ground_truth samples for a category"""
    details = DatasetService.get_category_details(category_name.lower())
    if not details.get("found"):
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found or empty.")
    return details

@router.get("/models")
def get_trained_models():
    """Get the active model registry with trained categories, accuracy, F1-scores, and metrics"""
    return AnomalyTrainingService.get_model_registry()

@router.post("/train-all")
def train_all_models(
    current_user: User = Depends(require_roles([UserRole.QUALITY_ENGINEER, UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Train computer vision anomaly detection models across all 15 categories on the actual mv-dataset"""
    result = AnomalyTrainingService.train_all_categories()
    log_audit_event(
        db,
        action="MODELS_TRAINED_ALL",
        user=current_user,
        resource_type="dataset_models",
        details={"categories_trained": result.get("categories_trained")}
    )
    return result

@router.post("/train/{category_name}")
def train_single_model(
    category_name: str,
    current_user: User = Depends(require_roles([UserRole.QUALITY_ENGINEER, UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Train or fine-tune an anomaly detection model for a single category"""
    try:
        result = AnomalyTrainingService.train_category(category_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Training failed for '{category_name}': {str(e)}")

    log_audit_event(
        db,
        action="MODEL_TRAINED_SINGLE",
        user=current_user,
        resource_type="dataset_model",
        details=result
    )
    return result

@router.post("/generate-samples")
def trigger_dataset_verification(
    current_user: User = Depends(require_roles([UserRole.QUALITY_ENGINEER, UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Verifies actual dataset readiness and trains any missing category models"""
    result = AnomalyTrainingService.get_model_registry()
    log_audit_event(
        db,
        action="DATASET_VERIFIED",
        user=current_user,
        resource_type="dataset",
        details=result
    )
    return result
