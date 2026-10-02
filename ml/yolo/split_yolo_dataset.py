import shutil
from pathlib import Path
import random

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
SOURCE_IMAGES = BASE_DIR / "dataset" / "images"
SOURCE_LABELS = BASE_DIR / "dataset" / "labels"

DATASET_DIR = BASE_DIR / "dataset"

# ============================================================
# SPLIT SETTINGS
# ============================================================

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# ============================================================
# CHECK SOURCE
# ============================================================

if not SOURCE_IMAGES.exists():
    raise FileNotFoundError(
        f"Images folder not found: {SOURCE_IMAGES}"
    )

# ============================================================
# CLEAN OLD SPLIT
# ============================================================

for split in ["train", "val", "test"]:

    split_dir = DATASET_DIR / split

    if split_dir.exists():
        shutil.rmtree(split_dir)

    (split_dir / "images").mkdir(
        parents=True,
        exist_ok=True
    )

    (split_dir / "labels").mkdir(
        parents=True,
        exist_ok=True
    )

# ============================================================
# GROUP IMAGES BY DEFECT TYPE
# ============================================================

groups = {
    "broken_large": [],
    "broken_small": [],
    "contamination": []
}

for image_path in SOURCE_IMAGES.glob("*.png"):

    filename = image_path.stem

    for defect_type in groups:

        if filename.startswith(defect_type + "_"):
            groups[defect_type].append(image_path)
            break

# ============================================================
# SPLIT EACH DEFECT TYPE
# ============================================================

print("=" * 60)
print("Creating stratified YOLO dataset split")
print("=" * 60)

total_counts = {
    "train": 0,
    "val": 0,
    "test": 0
}

for defect_type, images in groups.items():

    random.shuffle(images)

    total = len(images)

    train_end = int(total * TRAIN_RATIO)

    val_end = train_end + int(total * VAL_RATIO)

    train_images = images[:train_end]
    val_images = images[train_end:val_end]
    test_images = images[val_end:]

    splits = {
        "train": train_images,
        "val": val_images,
        "test": test_images
    }

    print(f"\n{defect_type}: {total} images")

    for split_name, split_images in splits.items():

        for image_path in split_images:

            label_path = SOURCE_LABELS / (
                image_path.stem + ".txt"
            )

            if not label_path.exists():
                print(
                    f"WARNING: Label missing for "
                    f"{image_path.name}"
                )
                continue

            # Copy image
            shutil.copy2(
                image_path,
                DATASET_DIR
                / split_name
                / "images"
                / image_path.name
            )

            # Copy label
            shutil.copy2(
                label_path,
                DATASET_DIR
                / split_name
                / "labels"
                / label_path.name
            )

            total_counts[split_name] += 1

        print(
            f"  {split_name}: "
            f"{len(split_images)}"
        )

# ============================================================
# FINAL SUMMARY
# ============================================================

total_images = sum(total_counts.values())

print("\n" + "=" * 60)
print("STRATIFIED YOLO DATASET SPLIT COMPLETED")
print("=" * 60)

print(f"Total images : {total_images}")
print(f"Training     : {total_counts['train']}")
print(f"Validation   : {total_counts['val']}")
print(f"Testing      : {total_counts['test']}")

print("=" * 60)