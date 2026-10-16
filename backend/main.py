from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.auth.auth import users, verify_password
from backend.upload.upload import router as upload_router
from backend.monitoring import router as monitoring_router


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="VisionInspect AI",
    description="AI-powered manufacturing quality inspection system",
    version="1.0.0"
)


# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# ROUTERS
# ==========================================

app.include_router(upload_router)

app.include_router(monitoring_router)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "VisionInspect AI Backend is running!"
    }


# ==========================================
# LOGIN
# ==========================================

class LoginRequest(BaseModel):

    username: str
    password: str


@app.post("/login")
def login(request: LoginRequest):

    user = users.get(request.username)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )


    if not verify_password(
        request.password,
        user["password"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )


    return {
        "message": "Login successful",
        "username": request.username
    }