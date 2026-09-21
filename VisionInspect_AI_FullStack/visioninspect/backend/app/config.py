"""
Central configuration for VisionInspect AI backend.
Reads from environment variables / .env file so secrets never live in code.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR}/visioninspect.db"
    jwt_secret_key: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    upload_dir: str = str(BASE_DIR / "uploads")
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

# Make sure the upload directory exists at import time
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(os.path.join(settings.upload_dir, "raw"), exist_ok=True)
os.makedirs(os.path.join(settings.upload_dir, "annotated"), exist_ok=True)
