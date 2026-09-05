from backend.app.api.inspection import router as inspection_router
from backend.app.core.dependencies import (require_admin,
require_quality_engineer)
from backend.app.api.prediction import router as prediction_router
from backend.app.models.user import User
from fastapi import Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router


app = FastAPI(
    title="VisionInspect AI",
    description="Manufacturing Defect Detection & Quality Inspection System",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication routes
app.include_router(auth_router)
app.include_router(inspection_router)
app.include_router(prediction_router)


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