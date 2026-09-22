"""
One-time migration: updates existing 'test_defect' image rows with the
specific defect type name from the MVTec AD folder structure (e.g.
'broken_large', 'scratch', 'contamination') instead of the generic
'test_defect' tag.

Run once, after load_mvtec_dataset.py has already loaded the dataset
(from the backend project root, with venv active):

    python update_defect_labels.py
"""

from pathlib import Path

from app.database import SessionLocal
from app import models

DATASET_IMAGES_DIR = Path("dataset_images")


def main():
    if not DATASET_IMAGES_DIR.exists():
        print("ERROR: dataset_images/ not found.")
        return

    db = SessionLocal()
    updated = 0

    categories = sorted([p for p in DATASET_IMAGES_DIR.iterdir() if p.is_dir()])
    for cat_dir in categories:
        test_dir = cat_dir / "test"
        if not test_dir.exists():
            continue

        for defect_folder in sorted(test_dir.iterdir()):
            if not defect_folder.is_dir() or defect_folder.name == "good":
                continue  # skip non-defect (good) test images

            label = defect_folder.name  # e.g. 'broken_large', 'scratch'

            for img_path in defect_folder.glob("*.png"):
                image = (
                    db.query(models.Image)
                    .filter(models.Image.image_path == str(img_path))
                    .first()
                )
                if image and not image.image_type.startswith("test_defect:"):
                    image.image_type = f"test_defect:{label}"
                    updated += 1

        db.commit()
        print(f"  {cat_dir.name}: done")

    db.close()
    print(f"\nUpdated {updated} image records with specific defect labels.")


if __name__ == "__main__":
    main()
