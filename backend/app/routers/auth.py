from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserLogin, UserResponse, Token
from ..services.auth_service import verify_password, get_password_hash, create_access_token
from ..utils.dependencies import get_current_user
from ..utils.logger import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Check if username or email exists
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered."
        )

    # Validate role
    valid_roles = [UserRole.QUALITY_ENGINEER, UserRole.FACTORY_SUPERVISOR, UserRole.PRODUCTION_MANAGER, UserRole.ADMIN]
    if user_in.role not in valid_roles:
        user_in.role = UserRole.QUALITY_ENGINEER

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        role=user_in.role,
        department=user_in.department or "Manufacturing Quality Control",
        hashed_password=get_password_hash(user_in.password),
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_audit_event(
        db,
        action="USER_REGISTER",
        user=db_user,
        resource_type="user",
        resource_id=str(db_user.id),
        ip_address=request.client.host if request.client else None
    )

    access_token = create_access_token(data={"sub": db_user.username, "role": db_user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(db_user)
    )

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    log_audit_event(
        db,
        action="USER_LOGIN",
        user=user,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None
    )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token login for Swagger UI"""
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.post("/switch-demo-role", response_model=Token)
def switch_demo_role(role: str, db: Session = Depends(get_db)):
    """Quick helper for testing different roles in UI demo mode"""
    valid_roles = {
        UserRole.QUALITY_ENGINEER: ("engineer@visioninspect.ai", "Alex Rivera (Quality Engineer)"),
        UserRole.FACTORY_SUPERVISOR: ("supervisor@visioninspect.ai", "Sarah Chen (Factory Supervisor)"),
        UserRole.PRODUCTION_MANAGER: ("manager@visioninspect.ai", "Marcus Vance (Production Manager)"),
    }
    
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail="Invalid demo role.")

    email, name = valid_roles[role]
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create demo user if not exists
        username = role.replace("_", ".")
        user = User(
            username=username,
            email=email,
            full_name=name,
            role=role,
            department="Industry 4.0 Operations",
            hashed_password=get_password_hash("password123"),
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )
