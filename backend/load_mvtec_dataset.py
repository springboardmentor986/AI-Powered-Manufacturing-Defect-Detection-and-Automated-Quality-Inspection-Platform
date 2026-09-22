"""
MVTec AD Dataset Loader for VisionInspect AI

Scans a local MVTec AD dataset folder and populates the `categories`
and `images` tables. Copies each image file into the backend's
`dataset_images/<category>/<split>/` folder so paths stay stable.

Usage (from the backend project root, with venv active):
    python load_mvtec_dataset.py "C:\\Users\\acer\\Downloads\\mvtec_ad"

Optional: limit how many images per category/split are loaded (useful
for a quick first test instead of loading all ~5,000 images):
    python load_mvtec_dataset.py "C:\\Users\\acer\\Downloads\\mvtec_ad" --limit 20
"""

import argparse
import shutil
import sys
from pathlib import Path

from app.database import SessionLocal, engine, Base
from app import models

# Categories that MVTec AD classifies as "texture" type vs "object" type
TEXTURE_CATEGORIES = {"carpet", "grid", "leather", "tile", "wood"}

DATASET_IMAGES_DIR = Path("dataset_images")


def get_or_create_category(db, name: str):
    category = db.query(models.Category).filter(models.Category.category_name == name).first()
    if category:
        return category

    category_type = "texture" if name in TEXTURE_CATEGORIES else "object"
    category = models.Category(
        category_name=name,
        category_type=category_type,
        dataset_name="MVTec AD",
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    print(f"  + created category: {name} ({category_type})")
    return category


def load_split(db, category, category_dir: Path, split: str, limit: int | None):
    """
    split is 'train' or 'test'. Under train/ there's only 'good'.
    Under test/ there can be 'good' plus one folder per defect type
    (e.g. broken_large, broken_small, contamination).
    """
    split_dir = category_dir / split
    if not split_dir.exists():
        return 0

    count = 0
    for subfolder in sorted(split_dir.iterdir()):
        if not subfolder.is_dir():
            continue

        is_good = subfolder.name == "good"
        dest_dir = DATASET_IMAGES_DIR / category.category_name / split / subfolder.name
        dest_dir.mkdir(parents=True, exist_ok=True)

        image_files = sorted(subfolder.glob("*.png"))
        if limit:
            image_files = image_files[:limit]

        for img_path in image_files:
            dest_path = dest_dir / img_path.name
            if not dest_path.exists():
                shutil.copy2(img_path, dest_path)

            image_type = "train" if split == "train" else ("test" if is_good else "test_defect")

            existing = (
                db.query(models.Image)
                .filter(models.Image.image_path == str(dest_path))
                .first()
            )
            if existing:
                continue

            image = models.Image(
                category_id=category.category_id,
                uploaded_by=None,
                image_path=str(dest_path),
                image_source="mvtec",
                image_type=image_type,
            )
            db.add(image)
            count += 1

        db.commit()
    return count


def main():
    parser = argparse.ArgumentParser(description="Load MVTec AD dataset into VisionInspect AI DB")
    parser.add_argument("dataset_path", help="Path to the extracted mvtec_ad folder")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max images to load per category/split/defect-folder (default: all)",
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset_path)
    if not dataset_root.exists():
        print(f"ERROR: dataset path not found: {dataset_root}")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    category_dirs = sorted(
        [p for p in dataset_root.iterdir() if p.is_dir() and (p / "train").exists()]
    )

    if not category_dirs:
        print("ERROR: no category folders with a 'train' subfolder found. "
              "Check that dataset_path points at the extracted mvtec_ad folder.")
        sys.exit(1)

    print(f"Found {len(category_dirs)} categories: {[c.name for c in category_dirs]}")
    print()

    total_images = 0
    for category_dir in category_dirs:
        name = category_dir.name
        print(f"Loading category: {name}")
        category = get_or_create_category(db, name)

        train_count = load_split(db, category, category_dir, "train", args.limit)
        test_count = load_split(db, category, category_dir, "test", args.limit)

        print(f"    train images added: {train_count}, test images added: {test_count}")
        total_images += train_count + test_count

    db.close()
    print()
    print(f"Done. Total images loaded into DB: {total_images}")


if __name__ == "__main__":
    main()
