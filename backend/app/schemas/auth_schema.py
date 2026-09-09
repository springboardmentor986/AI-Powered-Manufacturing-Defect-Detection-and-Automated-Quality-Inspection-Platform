from pydantic import BaseModel, EmailStr, field_validator

from app.security.roles import SUPPORTED_ROLE_IDS


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_id: int
    supervisor_registration_code: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        cleaned_name = name.strip()

        if not cleaned_name:
            raise ValueError("Name is required.")

        return cleaned_name

    @field_validator("role_id")
    @classmethod
    def validate_role_id(cls, role_id: int) -> int:
        if role_id not in SUPPORTED_ROLE_IDS:
            raise ValueError("Selected role is not supported.")

        return role_id

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter.")

        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one number.")

        if not any(not char.isalnum() for char in password):
            raise ValueError("Password must contain at least one special character.")

        return password

class LoginRequest(BaseModel):
    email : EmailStr
    password: str
