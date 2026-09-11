from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routers import auth, inspections, dataset

app = FastAPI(
    title="VisionInspect AI",
    description="AI-powered manufacturing defect detection - Milestone 2",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inspections.router)
app.include_router(dataset.router)

os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)
os.makedirs("results", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/processed", StaticFiles(directory="processed"), name="processed")
app.mount("/results", StaticFiles(directory="results"), name="results")

if os.path.exists("dataset"):
    app.mount("/dataset", StaticFiles(directory="dataset"), name="dataset")

@app.get("/")
def root():
    return {"message": "VisionInspect AI API", "version": "2.0.0", "milestone": 2}

@app.get("/health")
def health_check():
    return {"status": "healthy", "milestone": 2}
