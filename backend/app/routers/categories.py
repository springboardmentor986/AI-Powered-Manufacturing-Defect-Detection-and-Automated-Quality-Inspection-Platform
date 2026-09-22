from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[schemas.CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return db.query(models.Category).order_by(models.Category.category_name).all()


@router.post("/", response_model=schemas.CategoryOut)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("admin")),
):
    existing = (
        db.query(models.Category)
        .filter(models.Category.category_name == category.category_name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    new_category = models.Category(
        category_name=category.category_name,
        category_type=category.category_type,
        dataset_name=category.dataset_name,
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category