"""
Builds an anomaly-detection reference profile for every category found in
dataset_images/, using each category's 'good' training images.

Run this once after load_mvtec_dataset.py (from the backend project root,
with venv active):

    python build_references.py
"""

from pathlib import Path

from app.vision.detector import build_reference

DATASET_IMAGES_DIR = Path("dataset_images")


def main():
    if not DATASET_IMAGES_DIR.exists():
        print("ERROR: dataset_images/ not found. Run load_mvtec_dataset.py first.")
        return

    categories = sorted([p for p in DATASET_IMAGES_DIR.iterdir() if p.is_dir()])
    if not categories:
        print("ERROR: no categories found under dataset_images/.")
        return

    print(f"Found {len(categories)} categories.\n")

    for cat_dir in categories:
        good_dir = cat_dir / "train" / "good"
        if not good_dir.exists():
            print(f"  skip {cat_dir.name}: no train/good folder")
            continue

        image_paths = [str(p) for p in sorted(good_dir.glob("*.png"))]
        if not image_paths:
            print(f"  skip {cat_dir.name}: no images in train/good")
            continue

        result = build_reference(cat_dir.name, image_paths)
        print(f"  built reference for {result['category']} "
              f"({result['images_used']} images)")

    print("\nDone. Reference profiles saved to model_artifacts/")


if __name__ == "__main__":
    main()
