from backend.app.api.analytics import router as analytics_router
from backend.app.api.inspection import router as inspection_router
from backend.app.core.dependencies import (require_admin,
require_quality_engineer)
from backend.app.api.prediction import router as prediction_router
from backend.app.models.user import User
from fastapi import Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.reports import router as reports_router


app = FastAPI(
    title="VisionInspect AI",
    description="Manufacturing Defect Detection & Quality Inspection System",
    version="1.0.0"
)


import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# CORS configuration - allow all origins for tunneling and production
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local storage directory for static image access
Path("storage/uploads").mkdir(parents=True, exist_ok=True)
if Path("storage").exists():
    app.mount("/storage", StaticFiles(directory="storage"), name="storage")



# Authentication routes
app.include_router(auth_router)
app.include_router(inspection_router)
app.include_router(prediction_router)
app.include_router(analytics_router)
app.include_router(reports_router)

@app.get("/")
def root():
    return {
        "message": "VisionInspect AI API is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "VisionInspect AI Backend"
    }
@app.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "Welcome Admin!",
        "user": current_user.full_name,
        "role": current_user.role.name
    }
@app.get("/quality-test")
def quality_test(
    current_user: User = Depends(require_quality_engineer)
):
    return {
        "message": "Welcome Quality Engineer!",
        "user": current_user.full_name,
        "role": current_user.role.name
    }