from pathlib import Path
from ultralytics import YOLO
import time

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"D:\VisionInspectAI\ml")
YOLO_DIR = BASE_DIR / "yolo"

DATASETS_DIR = YOLO_DIR / "all_categories"
RUNS_DIR = YOLO_DIR / "runs"

# ============================================================
# ONLY THESE 3 CATEGORIES
# ============================================================

CATEGORIES = [
    "toothbrush",
    "transistor",
    "screw"
]

# ============================================================
# TRAINING SETTINGS
# ============================================================

EPOCHS = 100
IMAGE_SIZE = 800
BATCH_SIZE = 4
PATIENCE = 20

# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("VISIONINSPECT AI")
print("RETRAINING 3 DIFFICULT YOLO11n CATEGORIES")
print("=" * 70)

print("\nCategories:")
for category in CATEGORIES:
    print("  -", category)

print("\nTraining configuration:")
print("  Model      : YOLO11n")
print("  Epochs     :", EPOCHS)
print("  Image size :", IMAGE_SIZE)
print("  Batch size :", BATCH_SIZE)
print("  Patience   :", PATIENCE)
print("  Device     : CPU")

successful = []
failed = []

total_start = time.time()

# ============================================================
# TRAIN EACH CATEGORY
# ============================================================

for index, category in enumerate(CATEGORIES, start=1):

    print("\n")
    print("=" * 70)
    print(f"[{index}/3] RETRAINING: {category.upper()}")
    print("=" * 70)

    data_yaml = (
        DATASETS_DIR
        / category
        / "data.yaml"
    )

    if not data_yaml.exists():

        print("ERROR: data.yaml not found:")
        print(data_yaml)

        failed.append(category)
        continue

    try:

        # ----------------------------------------------------
        # Load fresh pretrained YOLO11n
        # ----------------------------------------------------

        model = YOLO("yolo11n.pt")

        print("\nStarting training...")

        start_time = time.time()

        model.train(

            data=str(data_yaml),

            # Training
            epochs=EPOCHS,
            imgsz=IMAGE_SIZE,
            batch=BATCH_SIZE,
            patience=PATIENCE,

            # Optimizer
            optimizer="AdamW",
            lr0=0.0005,
            lrf=0.01,
            weight_decay=0.0005,

            # Augmentation
            hsv_h=0.015,
            hsv_s=0.3,
            hsv_v=0.3,

            degrees=3.0,
            translate=0.08,
            scale=0.4,
            shear=1.0,

            fliplr=0.5,
            flipud=0.0,

            mosaic=0.5,
            mixup=0.0,

            # Reproducibility
            seed=42,

            # Pretrained weights
            pretrained=True,

            # Output
            project=str(RUNS_DIR),
            name=f"{category}_defect_retrained",
            exist_ok=True,

            plots=True,
            save=True
        )

        elapsed = time.time() - start_time

        print("\n" + "-" * 70)
        print(f"{category.upper()} RETRAINING COMPLETED")
        print(f"Time: {elapsed / 60:.2f} minutes")
        print("-" * 70)

        successful.append(category)

    except Exception as e:

        print("\n" + "-" * 70)
        print(f"{category.upper()} RETRAINING FAILED")
        print("Error:", e)
        print("-" * 70)

        failed.append(category)


# ============================================================
# FINAL SUMMARY
# ============================================================

total_time = time.time() - total_start

print("\n")
print("=" * 70)
print("RETRAINING SUMMARY")
print("=" * 70)

print("\nSuccessful:")
for category in successful:
    print("  [OK]", category)

print("\nFailed:")

if failed:
    for category in failed:
        print("  [FAILED]", category)
else:
    print("  None")

print("\n" + "-" * 70)

print(f"Successful: {len(successful)} / 3")
print(f"Failed:     {len(failed)} / 3")

print(f"\nTotal time: {total_time / 3600:.2f} hours")

print("\nNew models will be located under:")
print(RUNS_DIR)

print("\nNew run names:")
for category in CATEGORIES:
    print(f"  {category}_defect_retrained")

print("=" * 70)
print("RETRAINING FINISHED")
print("=" * 70)