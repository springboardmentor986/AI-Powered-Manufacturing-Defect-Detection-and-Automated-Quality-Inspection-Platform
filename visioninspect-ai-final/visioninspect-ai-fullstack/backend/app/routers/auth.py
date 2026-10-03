"""
Milestone 1 - Signup / login endpoints. First registered account becomes admin.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas, security
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=schemas.UserOut)
def signup(body: schemas.SignupRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == body.username).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")
    is_first_user = db.query(models.User).count() == 0
    user = models.User(
        username=body.username,
        full_name=body.username,
        role="admin" if is_first_user else body.role,
        hashed_password=security.hash_password(body.password),
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.post("/login", response_model=schemas.TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not security.verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")
    token = security.create_access_token(user.username, user.role)
    return {"access_token": token}

@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user
