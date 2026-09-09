from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth_schema import RegisterRequest, LoginRequest
from app.security.password import hash_password, verify_password
from app.security.roles import (
    ROLE_FACTORY_SUPERVISOR,
    SUPERVISOR_REGISTRATION_CODE,
    SUPPORTED_ROLE_IDS,
)

def register_user(db: Session, user_data: RegisterRequest):
    existing_user = (
        db.query(User).filter(User.email == user_data.email).first()
    )

    if existing_user:
        raise ValueError("Email already exists")

    if user_data.role_id not in SUPPORTED_ROLE_IDS:
        raise ValueError("Selected role is not supported")

    if (
        user_data.role_id == ROLE_FACTORY_SUPERVISOR
        and user_data.supervisor_registration_code != SUPERVISOR_REGISTRATION_CODE
    ):
        raise ValueError("A valid supervisor registration code is required")

    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        role_id=user_data.role_id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

def login_user(db: Session, user_data: LoginRequest):
    user = (
        db.query(User).filter(User.email==user_data.email).first()
    )

    if not user:
        raise ValueError("Invalid email or password")
    
    if not verify_password(user_data.password, user.password_hash):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("This account is inactive")

    return user
