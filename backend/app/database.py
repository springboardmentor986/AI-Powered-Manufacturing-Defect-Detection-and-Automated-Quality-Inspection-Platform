from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "visioninspect")

client = MongoClient(MONGO_URL)
database = client[DB_NAME]

users_collection = database["users"]
products_collection = database["products"]
inspections_collection = database["inspections"]

print(f"✅ Connected to MongoDB: {DB_NAME}")
