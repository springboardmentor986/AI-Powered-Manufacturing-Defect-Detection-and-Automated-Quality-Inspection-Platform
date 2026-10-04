import base64
import hashlib
import hmac
import json
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).resolve().parent))
from anomaly_detector import detect_defects
from defect_model import load_model

app = FastAPI(title="VisionInspect AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
DATABASE_PATH = Path(__file__).resolve().parent / "visioninspect.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
TOKEN_SECRET = os.getenv("VISIONINSPECT_TOKEN_SECRET", "visioninspect-demo-secret-change-in-production").encode()
DEMO_USERS = {
    "engineer@factory.com": {"password": "password123", "name": "Maya Chen", "role": "Quality Engineer"},
    "supervisor@factory.com": {"password": "supervisor123", "name": "Owen Brooks", "role": "Factory Supervisor"},
    "admin@factory.com": {"password": "admin12345", "name": "Avery Singh", "role": "Administrator"},
}
ROLE_PERMISSIONS = {
    "Administrator": {"inspect", "view_analytics", "manage_users", "view_audit"},
    "Quality Engineer": {"inspect", "view_analytics"},
    "Factory Supervisor": {"inspect", "view_analytics", "view_audit"},
}


def is_ground_truth_mask(filename):
    return Path(filename or "").stem.lower().endswith("_mask")


def database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    for email, user in DEMO_USERS.items():
        connection.execute(
            "INSERT OR IGNORE INTO users (email, name, role, password_hash, active, created_at) VALUES (?, ?, ?, ?, 1, ?)",
            (email, user["name"], user["role"], hash_password(user["password"]), utc_now()),
        )
    connection.commit()
    return connection


def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180_000).hex()
    return f"pbkdf2_sha256$180000${salt}${digest}"


def verify_password(password, stored_hash):
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return algorithm == "pbkdf2_sha256" and hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def find_user(email):
    with database() as connection:
        row = connection.execute("SELECT email, name, role, password_hash, active, created_at FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def require_permission(user, permission):
    if permission not in ROLE_PERMISSIONS.get(user["role"], set()):
        raise HTTPException(status_code=403, detail=f"{user['role']} cannot perform {permission}")


def load_inspections():
    with database() as connection:
        rows = connection.execute("SELECT payload FROM inspections ORDER BY created_at ASC").fetchall()
    return [json.loads(row["payload"]) for row in rows]


def save_inspection(record):
    with database() as connection:
        connection.execute("INSERT INTO inspections VALUES (?, ?, ?)", (record["id"], record["timestamp"], json.dumps(record)))
        connection.commit()


def audit(actor, action, metadata):
    with database() as connection:
        connection.execute("INSERT INTO audit_log (created_at, actor, action, metadata) VALUES (?, ?, ?, ?)", (utc_now(), actor, action, json.dumps(metadata)))
        connection.commit()


def create_token(email):
    expires = int(time.time()) + 8 * 60 * 60
    body = f"{email}:{expires}"
    signature = hmac.new(TOKEN_SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}:{signature}"


def current_user(authorization):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        email, expires, signature = authorization[7:].split(":", 2)
        body = f"{email}:{expires}"
        expected = hmac.new(TOKEN_SECRET, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected) or int(expires) < int(time.time()):
            raise ValueError
        user = find_user(email)
        if not user or not user["active"]:
            raise ValueError
        return {"email": email, "name": user["name"], "role": user["role"]}
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def public_inspection(result):
    return {key: value for key, value in result.items() if key != "annotated_image"}


def analytics_summary():
    history = load_inspections()
    total = len(history)
    defective = sum(item["is_defective"] for item in history)
    type_counts = {"contamination": 0, "broken_small": 0, "broken_large": 0}
    for item in history:
        if item["is_defective"] and item["defect_type"] in type_counts:
            type_counts[item["defect_type"]] += 1
    return {
        "total_inspections": total,
        "good_count": total - defective,
        "bad_count": defective,
        "pass_rate": round(((total - defective) / total * 100) if total else 0, 1),
        "defect_counts": type_counts,
        "average_severity": round(sum(item["severity_score"] for item in history) / total, 1) if total else 0,
        "recent": history[-8:][::-1],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "VisionInspect AI"}


@app.post("/api/auth/login")
async def login(payload: dict):
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    user = find_user(email)
    if user is None or not user["active"] or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    audit(email, "login", {"role": user["role"]})
    return {"token": create_token(email), "email": email, "name": user["name"], "role": user["role"], "permissions": sorted(ROLE_PERMISSIONS[user["role"]])}


@app.post("/api/users")
async def create_user(payload: dict, authorization: str | None = Header(default=None)):
    actor = current_user(authorization)
    require_permission(actor, "manage_users")
    email = str(payload.get("email", "")).strip().lower()
    name = str(payload.get("name", "")).strip()
    role = str(payload.get("role", "Quality Engineer")).strip()
    password = str(payload.get("password", ""))
    if "@" not in email or not name or len(password) < 8 or role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="Provide a valid email, name, role, and password of at least 8 characters")
    try:
        with database() as connection:
            connection.execute("INSERT INTO users (email, name, role, password_hash, active, created_at) VALUES (?, ?, ?, ?, 1, ?)", (email, name, role, hash_password(password), utc_now()))
            connection.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="A user with that email already exists") from exc
    audit(actor["email"], "user_created", {"email": email, "role": role})
    return {"email": email, "name": name, "role": role, "active": True}


@app.get("/api/users")
def list_users(authorization: str | None = Header(default=None)):
    actor = current_user(authorization)
    require_permission(actor, "manage_users")
    with database() as connection:
        rows = connection.execute("SELECT email, name, role, active, created_at FROM users ORDER BY created_at ASC").fetchall()
    return {"items": [dict(row) for row in rows]}


@app.patch("/api/users/{email}")
async def update_user(email: str, payload: dict, authorization: str | None = Header(default=None)):
    actor = current_user(authorization)
    require_permission(actor, "manage_users")
    target = find_user(email.lower())
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    name = str(payload.get("name", target["name"])).strip()
    role = str(payload.get("role", target["role"])).strip()
    active = 1 if payload.get("active", bool(target["active"])) else 0
    if not name or role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="Invalid name or role")
    with database() as connection:
        connection.execute("UPDATE users SET name = ?, role = ?, active = ? WHERE email = ?", (name, role, active, email.lower()))
        connection.commit()
    audit(actor["email"], "user_updated", {"email": email.lower(), "role": role, "active": bool(active)})
    return {"email": email.lower(), "name": name, "role": role, "active": bool(active)}


@app.get("/api/audit")
def get_audit(authorization: str | None = Header(default=None)):
    actor = current_user(authorization)
    require_permission(actor, "view_audit")
    with database() as connection:
        rows = connection.execute("SELECT id, created_at, actor, action, metadata FROM audit_log ORDER BY id DESC LIMIT 100").fetchall()
    return {"items": [{**dict(row), "metadata": json.loads(row["metadata"])} for row in rows]}


@app.get("/api/analytics")
def get_analytics(authorization: str | None = Header(default=None)):
    require_permission(current_user(authorization), "view_analytics")
    return analytics_summary()


@app.get("/api/metrics")
def get_metrics(authorization: str | None = Header(default=None)):
    require_permission(current_user(authorization), "view_analytics")
    history = load_inspections()
    durations = [item["processing_ms"] for item in history if "processing_ms" in item]
    return {
        "inspection_count": len(history),
        "average_processing_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        "fastest_processing_ms": round(min(durations), 2) if durations else 0,
        "slowest_processing_ms": round(max(durations), 2) if durations else 0,
        "automation_rate": 100.0 if history else 0.0,
    }


@app.get("/api/model")
def get_model_info(authorization: str | None = Header(default=None)):
    require_permission(current_user(authorization), "view_analytics")
    model = load_model()
    return {
        "name": "VisionInspect bottle-only hierarchical random forest",
        "version": model["version"],
        "feature_count": model["feature_count"],
        "training_samples": sum(model["sample_counts"].values()),
        "sample_counts": model["sample_counts"],
        "classes": model["labels"],
    }


@app.get("/api/inspections")
def get_inspections(limit: int = 50, authorization: str | None = Header(default=None)):
    require_permission(current_user(authorization), "view_analytics")
    history = load_inspections()
    return {"items": history[-max(1, min(limit, 100)):][::-1]}


@app.post("/api/inspect")
async def inspect_image(
    file: UploadFile = File(...),
    operator: str = Form("Quality Engineer"),
    source: str = Form("Manual upload"),
    batch_id: str = Form("single-inspection"),
    authorization: str | None = Header(default=None),
):
    try:
        actor = current_user(authorization)
        require_permission(actor, "inspect")
        if is_ground_truth_mask(file.filename):
            raise HTTPException(
                status_code=400,
                detail="This looks like a ground-truth mask, not a product photo. Upload the original image instead.",
            )
        started_at = time.perf_counter()
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Image exceeds the 10 MB upload limit.")
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Please upload a valid image file.")
        img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Image could not be decoded.")

        result = detect_defects(img)
        _, buffer = cv2.imencode(".png", result["annotated_image"])
        record = {
            **public_inspection(result),
            "id": f"INSP-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": utc_now(),
            "filename": file.filename or "uploaded-image",
            "operator": operator or actor["role"],
            "source": source,
            "batch_id": batch_id,
            "image_width": int(img.shape[1]),
            "image_height": int(img.shape[0]),
            "processing_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "annotated_image_base64": f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}",
        }
        save_inspection(record)
        audit(actor["email"], "inspection_created", {"inspection_id": record["id"], "classification": record["classification"]})
        return record
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
