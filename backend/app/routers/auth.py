from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest, LoginRequest
from app.services.auth_service import register_user, login_user
from app.security.jwt import create_access_token
from app.security.dependencies import get_current_user
from app.security.authorization import require_role

router = APIRouter(prefix="/auth", tags=["Authentication"])


def serialize_user(db: Session, user: User):
    role = db.query(Role).filter(Role.id == user.role_id).first()

    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role_id": user.role_id,
        "role": role.role if role else None,
    }


@router.post("/register")
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, user_data)
        return serialize_user(db, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/login")
def login(user_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = login_user(db, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    if user.role_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has no assigned role",
        )

    access_token = create_access_token(
        user_id=user.id,
        role_id=user.role_id
    )

    return {
        "access_token": access_token,
        "access token": access_token,
        "token_type": "bearer",
        "user": serialize_user(db, user),
    }

@router.get("/me")
def get_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
        )

    return serialize_user(db, user)

@router.get("/supervisor-test")
def supervisor_test(
    current_user=Depends(require_role(2))
):
    return {
        "message": "Factory Supervisor access granted",
        "user": current_user
    }
