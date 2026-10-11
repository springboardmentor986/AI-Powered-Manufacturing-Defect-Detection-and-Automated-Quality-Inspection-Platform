import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "VisionInspect AI"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "visioninspect-super-secret-production-key-2026-secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/visioninspect.db")
    
    # File Storage Paths
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = BASE_DIR / "data" / "uploads"
    THUMBNAILS_DIR: Path = BASE_DIR / "data" / "thumbnails"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    HEATMAPS_DIR: Path = BASE_DIR / "data" / "heatmaps"
    MVTEC_DIR: Path = BASE_DIR / "data" / "mvtec_ad"
    WORKSPACE_MAIN_DATA_DIR: Path = BASE_DIR.parent / "main data"
    
    # Priority dataset path resolution
    @property
    def ACTIVE_DATASET_DIR(self) -> Path:
        if self.WORKSPACE_MAIN_DATA_DIR.exists() and any(self.WORKSPACE_MAIN_DATA_DIR.iterdir()):
            return self.WORKSPACE_MAIN_DATA_DIR
        return self.MVTEC_DIR
    
    # Allowed File Extensions & Limits
    ALLOWED_EXTENSIONS: set = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    MAX_FILE_SIZE_MB: int = 25
    
    # MVTec AD Standard 15 Categories
    MVTEC_CATEGORIES: list = [
        "bottle",
        "cable",
        "capsule",
        "carpet",
        "grid",
        "hazelnut",
        "leather",
        "metal_nut",
        "pill",
        "screw",
        "tile",
        "toothbrush",
        "transistor",
        "wood",
        "zipper"
    ]

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.HEATMAPS_DIR.mkdir(parents=True, exist_ok=True)
settings.MVTEC_DIR.mkdir(parents=True, exist_ok=True)
