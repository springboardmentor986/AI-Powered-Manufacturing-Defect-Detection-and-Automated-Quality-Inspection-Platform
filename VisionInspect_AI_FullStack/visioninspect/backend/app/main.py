from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import auth, users, images, inspections, analytics

# Create tables if they don't exist yet (fine for SQLite/dev; use Alembic
# migrations instead if you move to Postgres in production).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VisionInspect AI",
    description="AI-powered manufacturing defect detection & quality inspection platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(images.router)
app.include_router(inspections.router)
app.include_router(analytics.router)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "VisionInspect AI backend"}
