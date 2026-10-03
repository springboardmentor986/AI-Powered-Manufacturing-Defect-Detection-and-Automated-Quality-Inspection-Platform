"""
Milestone 1 - User management (admin / factory_supervisor only), matches the
Users page in the demo app.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..deps import require_roles

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db),
                _=Depends(require_roles("admin", "factory_supervisor"))):
    return db.query(models.User).all()

@router.patch("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, body: schemas.RoleUpdate, db: Session = Depends(get_db),
                 _=Depends(require_roles("admin"))):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.commit(); db.refresh(user)
    return user
