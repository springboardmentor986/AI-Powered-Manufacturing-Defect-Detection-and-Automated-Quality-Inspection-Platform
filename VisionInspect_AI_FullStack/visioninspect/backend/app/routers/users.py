from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import User, UserRole
from app.schemas import UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin, UserRole.factory_supervisor)),
):
    """User Management Module: list all accounts. Admin & factory supervisors only."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    role: UserRole,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin)),
):
    """Role management: change a user's role. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
