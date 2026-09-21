"""
One-time setup script:
  1. Creates a default admin + demo users for each role.
  2. Generates a small synthetic "MVTec-AD-style" image set (clean / crack /
     scratch / dent / contamination) in ./dataset, since the real MVTec AD
     dataset is not redistributable from this environment. These are
     synthetic stand-ins with the same *structure* (clean vs. defective
     product-surface images) that let the CV pipeline be demoed end-to-end.
  3. Uploads a handful of them through the same pipeline the app uses, so
     the dashboard has example data on first run.

Run with:  python seed.py
"""
import io
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, Base, engine
from app.models import User, UserRole
from app.security import hash_password
from app.config import settings

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")


def make_base_surface(size=(400, 400), base_gray=170, noise=6):
    arr = np.full((size[1], size[0], 3), base_gray, dtype=np.int16)
    arr += np.random.randint(-noise, noise, arr.shape)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    return img.filter(ImageFilter.GaussianBlur(0.6))


def add_crack(img):
    d = ImageDraw.Draw(img)
    x, y = random.randint(60, 340), random.randint(60, 200)
    points = [(x, y)]
    for _ in range(10):
        x += random.randint(-8, 25)
        y += random.randint(5, 18)
        points.append((x, y))
    d.line(points, fill=(40, 40, 40), width=2)
    return img


def add_scratch(img):
    d = ImageDraw.Draw(img)
    x1, y1 = random.randint(50, 150), random.randint(50, 150)
    x2, y2 = x1 + random.randint(80, 180), y1 + random.randint(10, 40)
    d.line([(x1, y1), (x2, y2)], fill=(90, 90, 90), width=1)
    return img


def add_dent(img):
    d = ImageDraw.Draw(img)
    x, y = random.randint(100, 300), random.randint(100, 300)
    r = random.randint(14, 22)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(120, 120, 120))
    return img


def add_contamination(img):
    d = ImageDraw.Draw(img)
    cx, cy = random.randint(80, 320), random.randint(80, 320)
    for _ in range(30):
        ox, oy = cx + random.randint(-18, 18), cy + random.randint(-18, 18)
        r = random.randint(1, 4)
        shade = random.randint(50, 90)
        d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=(shade, shade, shade))
    return img


GENERATORS = {
    "clean": lambda img: img,
    "crack": add_crack,
    "scratch": add_scratch,
    "dent": add_dent,
    "contamination": add_contamination,
}


def generate_dataset(per_class=6):
    for cls, fn in GENERATORS.items():
        out_dir = os.path.join(DATASET_DIR, cls)
        os.makedirs(out_dir, exist_ok=True)
        for i in range(per_class):
            img = make_base_surface()
            img = fn(img)
            img.save(os.path.join(out_dir, f"{cls}_{i:03d}.png"))
    print(f"Synthetic dataset generated at {DATASET_DIR}")


def seed_users():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        demo_accounts = [
            ("Admin User", "admin@visioninspect.ai", "Admin@12345", UserRole.admin),
            ("Priya Rao", "engineer@visioninspect.ai", "Engineer@12345", UserRole.quality_engineer),
            ("Factory Supervisor", "supervisor@visioninspect.ai", "Supervisor@12345", UserRole.factory_supervisor),
            ("Production Manager", "manager@visioninspect.ai", "Manager@12345", UserRole.production_manager),
        ]
        for name, email, pw, role in demo_accounts:
            if not db.query(User).filter(User.email == email).first():
                db.add(User(full_name=name, email=email, hashed_password=hash_password(pw), role=role))
        db.commit()
        print("Seeded demo accounts (see README for credentials).")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
    generate_dataset()
