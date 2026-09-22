from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import users, images, categories, inspections, analytics

app = FastAPI(title="VisionInspect AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(images.router)
app.include_router(categories.router)
app.include_router(inspections.router)
app.include_router(analytics.router)



@app.get("/")
def root():
    return {"message": "VisionInspect AI backend running"}
