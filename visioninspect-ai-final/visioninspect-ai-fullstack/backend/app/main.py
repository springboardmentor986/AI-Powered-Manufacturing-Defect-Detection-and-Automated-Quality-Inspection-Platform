"""
Milestone 1 - FastAPI app entrypoint: CORS, DB table creation, router wiring.
Run locally with:  uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .config import settings
from .routers import auth, users, inspections, analytics, validation

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="VisionInspect AI", version="1.0.0",
              description="AI-powered manufacturing defect detection and quality inspection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(inspections.router)
app.include_router(analytics.router)
app.include_router(validation.router)

@app.get("/health")
def health():
    return {"status": "ok"}
