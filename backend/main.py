from database.connection import Base, engine
from models.user import User

from models.inspection import Inspection
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from routes.inspection import router as inspection_router

app = FastAPI(
    title="VisionInspect AI",
    description="AI Manufacturing Defect Detection & Quality Inspection System",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {
        "message": "Welcome to VisionInspect AI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(auth_router)
app.include_router(inspection_router)