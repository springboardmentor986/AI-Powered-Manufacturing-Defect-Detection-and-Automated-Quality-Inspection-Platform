from fastapi import APIRouter, HTTPException, status, Form
from datetime import datetime, timedelta
from jose import jwt
import hashlib
import os
from dotenv import load_dotenv
from app.database import users_collection, products_collection

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def seed_database():
    if products_collection.count_documents({}) == 0:
        products = [
            {"product_name": "Metal Component", "product_code": "MC-001"},
            {"product_name": "Plastic Part", "product_code": "PP-001"},
            {"product_name": "Electronic Board", "product_code": "EB-001"},
            {"product_name": "Glass Panel", "product_code": "GP-001"},
            {"product_name": "Rubber Seal", "product_code": "RS-001"},
            {"product_name": "Textile Roll", "product_code": "TR-001"},
        ]
        products_collection.insert_many(products)
        print("✅ Products seeded")
    
    if users_collection.count_documents({}) == 0:
        users = [
            {"name": "Rahul Kumar", "email": "engineer@gmail.com", "password": get_password_hash("password123"), "role": "quality_engineer"},
            {"name": "Anil Singh", "email": "supervisor@gmail.com", "password": get_password_hash("password123"), "role": "supervisor"},
        ]
        users_collection.insert_many(users)
        print("✅ Users seeded")

@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...)
):
    seed_database()
    
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@router.get("/products")
def get_products():
    products = list(products_collection.find())
    for p in products:
        p["id"] = str(p["_id"])
    return products
