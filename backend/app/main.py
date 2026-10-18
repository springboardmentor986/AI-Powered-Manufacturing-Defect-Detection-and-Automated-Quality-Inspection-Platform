from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import engine, Base
from .routers import auth, inspections, dataset, dashboard, audit
from .models import user, inspection, audit as audit_model
from .services.dataset_service import DatasetService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    # Verify real MVTec AD dataset presence
    categories = DatasetService.get_available_categories()
    loaded_cats = [c for c in categories if c["is_loaded"]]
    total_imgs = sum(c["total_images"] for c in loaded_cats)
    print(f"[*] VisionInspect AI Startup: Real MVTec AD Dataset connected with {len(loaded_cats)}/{len(categories)} categories and {total_imgs} total images from {settings.ACTIVE_DATASET_DIR}")
    yield
    # Shutdown logic if any

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="VisionInspect AI — Manufacturing Defect Detection & Quality Inspection System API",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directories for images & thumbnails
app.mount("/static/uploads", StaticFiles(directory=str(settings.UPLOADS_DIR)), name="uploads")
app.mount("/static/thumbnails", StaticFiles(directory=str(settings.THUMBNAILS_DIR)), name="thumbnails")
app.mount("/static/processed", StaticFiles(directory=str(settings.PROCESSED_DIR)), name="processed")
app.mount("/static/heatmaps", StaticFiles(directory=str(settings.HEATMAPS_DIR)), name="heatmaps")
app.mount("/static/mvtec", StaticFiles(directory=str(settings.ACTIVE_DATASET_DIR)), name="mvtec")

# Include API Routers under /api/v1
api_v1_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(inspections.router, prefix=api_v1_prefix)
app.include_router(dataset.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(audit.router, prefix=api_v1_prefix)

@app.get("/")
def root_status():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "ONLINE",
        "docs_url": "/docs",
        "api_v1": api_v1_prefix
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "storage": {
            "uploads": settings.UPLOADS_DIR.exists(),
            "thumbnails": settings.THUMBNAILS_DIR.exists(),
            "mvtec": settings.ACTIVE_DATASET_DIR.exists()
        }
    }
