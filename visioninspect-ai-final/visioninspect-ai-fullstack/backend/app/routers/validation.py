"""
Milestone 4 - Run the validation suite on demand: generate a labeled
synthetic dataset, run the real pipeline on it, and return precision /
recall / F1 / mAP / confusion matrix. Mirrors the in-browser "Validation &
Testing" page, and reuses the same scripts in backend/validation/.
"""
from fastapi import APIRouter, Depends
from .. import models, schemas
from ..deps import require_roles
from validation.generate_labeled_dataset import generate_dataset
from validation.evaluate import evaluate

router = APIRouter(prefix="/validation", tags=["validation"])

@router.post("/run", response_model=schemas.ValidationResult)
def run_validation(n_images: int = 25,
                    _=Depends(require_roles("admin", "quality_engineer", "factory_supervisor"))):
    dataset = generate_dataset(n_images=n_images)
    result = evaluate(dataset)
    return result
