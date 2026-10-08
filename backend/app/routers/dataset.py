from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.dataset_service import DatasetService
from ..models.user import User, UserRole
from ..utils.dependencies import get_current_user, require_roles
from ..utils.logger import log_audit_event

router = APIRouter(prefix="/dataset", tags=["MVTec AD Dataset Explorer"])

@router.get("/categories", response_model=List[Dict[str, Any]])
def list_categories():
    """List all 15 MVTec AD categories, load status, and counts"""
    return DatasetService.get_available_categories()

@router.get("/category/{category_name}")
def get_category_details(category_name: str):
    """Get detailed train/test/ground_truth samples for a category"""
    details = DatasetService.get_category_details(category_name.lower())
    if not details.get("found"):
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found or empty.")
    return details

@router.post("/generate-samples")
def generate_samples(
    current_user: User = Depends(require_roles([UserRole.QUALITY_ENGINEER, UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Seed or regenerate synthetic MVTec AD sample textures and defect masks"""
    result = DatasetService.generate_sample_dataset()
    log_audit_event(
        db,
        action="DATASET_SEEDED",
        user=current_user,
        resource_type="dataset",
        details=result
    )
    return result
