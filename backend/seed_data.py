import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random
import shutil
import uuid
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import engine, SessionLocal, Base
from app.models.user import User, UserRole
from app.models.inspection import InspectionRecord, BatchInspection, InspectionStatus, QualityDecision
from app.models.audit import SystemAuditLog
from app.services.auth_service import get_password_hash
from app.services.dataset_service import DatasetService
from app.services.image_service import ImageService
from app.config import settings

def seed_database():
    print("[*] Initializing Database & Seeding Milestone 1 Data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Seed Demo Users
    users_data = [
        {
            "username": "quality.engineer",
            "email": "engineer@visioninspect.ai",
            "full_name": "Alex Rivera",
            "role": UserRole.QUALITY_ENGINEER,
            "department": "Line A Quality Inspection"
        },
        {
            "username": "factory.supervisor",
            "email": "supervisor@visioninspect.ai",
            "full_name": "Sarah Chen",
            "role": UserRole.FACTORY_SUPERVISOR,
            "department": "Manufacturing Operations"
        },
        {
            "username": "production.manager",
            "email": "manager@visioninspect.ai",
            "full_name": "Marcus Vance",
            "role": UserRole.PRODUCTION_MANAGER,
            "department": "Plant Management"
        }
    ]

    created_users = {}
    for u in users_data:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            new_user = User(
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                department=u["department"],
                hashed_password=get_password_hash("password123"),
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            created_users[u["role"]] = new_user
            print(f"  [+] Created user: {u['email']} [{u['role']}]")
        else:
            created_users[u["role"]] = existing
            print(f"  [.] User exists: {u['email']}")

    # 2. Seed Synthetic MVTec AD Categories
    print("[*] Generating MVTec AD Dataset Sample Structure...")
    dataset_res = DatasetService.generate_sample_dataset()
    print(f"  [+] {dataset_res['message']}")

    # 3. Seed Sample Inspection Records from MVTec AD
    print("[*] Seeding Initial Inspection Records...")
    engineer_user = created_users.get(UserRole.QUALITY_ENGINEER)
    
    # Create sample batch
    sample_batch = db.query(BatchInspection).filter(BatchInspection.batch_name == "BATCH-2026-08-A1").first()
    if not sample_batch:
        sample_batch = BatchInspection(
            batch_name="BATCH-2026-08-A1",
            description="Conveyor Line 1 Morning Batch Quality Check",
            category="capsule",
            total_images=6,
            processed_images=6,
            pass_count=4,
            fail_count=2,
            review_count=0,
            status="COMPLETED",
            created_by=engineer_user.id if engineer_user else None,
            created_at=datetime.now(timezone.utc) - timedelta(hours=3)
        )
        db.add(sample_batch)
        db.commit()
        db.refresh(sample_batch)

    # Seed 10 realistic inspections
    sample_categories = [
        ("capsule", "test", "crack", QualityDecision.FAIL, "High", 74.2),
        ("bottle", "test", "broken_small", QualityDecision.FAIL, "Critical", 88.5),
        ("metal_nut", "test", "good", QualityDecision.PASS, "Low", 11.3),
        ("screw", "test", "good", QualityDecision.PASS, "Low", 8.9),
        ("carpet", "test", "cut", QualityDecision.FAIL, "High", 68.0),
        ("tile", "test", "good", QualityDecision.PASS, "Low", 14.5),
        ("leather", "test", "color", QualityDecision.FAIL, "Medium", 52.1),
        ("wood", "test", "good", QualityDecision.PASS, "Low", 9.4),
        ("toothbrush", "test", "defective", QualityDecision.FAIL, "High", 81.0),
        ("transistor", "test", "good", QualityDecision.PASS, "Low", 12.0),
    ]

    for idx, (cat, split, defect, decision, sev_lvl, sev_score) in enumerate(sample_categories):
        img_name = "000.png"
        src_path = settings.MVTEC_DIR / cat / split / defect / img_name
        if src_path.exists():
            new_id = str(uuid.uuid4())
            save_name = f"{new_id}.png"
            thumb_name = f"thumb_{new_id}.png"
            
            dest_img = settings.UPLOADS_DIR / save_name
            dest_thumb = settings.THUMBNAILS_DIR / thumb_name

            shutil.copyfile(src_path, dest_img)

            img = Image.open(dest_img)
            thumb = img.copy()
            if thumb.mode in ("RGBA", "P"):
                thumb = thumb.convert("RGB")
            thumb.thumbnail((280, 280), Image.Resampling.LANCZOS)
            thumb.save(dest_thumb, format="PNG")

            meta = ImageService.extract_image_metadata(img)
            img_bytes = dest_img.read_bytes()

            rec = InspectionRecord(
                id=new_id,
                batch_id=sample_batch.id if idx < 4 else None,
                image_filename=save_name,
                image_path=str(dest_img),
                thumbnail_path=str(dest_thumb),
                original_filename=f"{cat}_{defect}_{idx+1}.png",
                file_size_bytes=len(img_bytes),
                image_width=meta["width"],
                image_height=meta["height"],
                color_channels=meta["channels"],
                file_format="PNG",
                image_hash=ImageService.compute_hash(img_bytes),
                category=cat,
                split=split,
                defect_type=defect,
                status=InspectionStatus.INSPECTED,
                quality_decision=decision,
                confidence_score=round(0.92 + (idx % 8) * 0.01, 3),
                severity_score=sev_score,
                severity_level=sev_lvl,
                inspection_metadata=meta,
                notes=f"Automated quality evaluation for {cat} ({defect}).",
                uploaded_by=engineer_user.id if engineer_user else None,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=15 * idx)
            )
            db.add(rec)
    
    db.commit()
    print("  [+] Seeded sample inspection records.")

    # 4. Seed Audit Logs
    audit_events = [
        ("SYSTEM_INIT", "System initialized and tables created"),
        ("USER_LOGIN", "Quality Engineer logged into Station A"),
        ("BATCH_CREATED", "Batch BATCH-2026-08-A1 submitted for line inspection"),
        ("DATASET_SEEDED", "MVTec AD synthetic test categories loaded")
    ]
    for action, detail in audit_events:
        log = SystemAuditLog(
            user_id=engineer_user.id if engineer_user else None,
            user_email="engineer@visioninspect.ai",
            action=action,
            resource_type="system",
            details={"info": detail},
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=30)
        )
        db.add(log)
    db.commit()
    db.close()
    print("[+] Milestone 1 Database Seeding Complete!")

if __name__ == "__main__":
    seed_database()
