from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from auth.dependencies import require_role
from schemas.user import UserCreate, UserLogin
from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token
)
from database.connection import get_db
from models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(
        user.password
    )

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role.value
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": str(new_user.id),
        "role": new_user.role
    }


@router.post("/login")
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        user.password,
        existing_user.password
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token_data = {
        "user_id": str(existing_user.id),
        "role": existing_user.role
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": existing_user.role
    }


@router.post("/refresh")
def refresh_access_token(
    refresh_token: str
):

    payload = decode_refresh_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    token_data = {
        "user_id": payload.get("user_id"),
        "role": payload.get("role")
    }

    new_access_token = create_access_token(token_data)

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "You are authenticated!",
        "user": current_user
    }


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    user = db.query(User).filter(User.id == int(current_user["user_id"])).first()
    if not user or not verify_password(current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.password = hash_password(new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.get("/quality-engineer")
def quality_engineer_area(
    current_user: dict = Depends(
        require_role("quality_engineer")
    )
):
    return {
        "message": "Welcome Quality Engineer",
        "user": current_user
    }


@router.get("/factory-supervisor")
def factory_supervisor_area(
    current_user: dict = Depends(
        require_role("factory_supervisor")
    )
):
    return {
        "message": "Welcome Factory Supervisor",
        "user": current_user
    }