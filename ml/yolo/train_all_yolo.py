from pathlib import Path
from ultralytics import YOLO
import torch
import traceback

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "all_categories"
RUNS_DIR = BASE_DIR / "runs"

# ============================================================
# ALL 15 MVTEC CATEGORIES
# ============================================================

CATEGORIES = [
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper"
]

# ============================================================
# TRAINING SETTINGS
# ============================================================

EPOCHS = 30
IMAGE_SIZE = 640
BATCH_SIZE = 8
PATIENCE = 10

DEVICE = 0 if torch.cuda.is_available() else "cpu"

# ============================================================
# TRAIN EACH CATEGORY
# ============================================================

successful = []
failed = []

print("=" * 70)
print("VISIONINSPECT AI - ALL 15 YOLO DEFECT DETECTORS")
print("=" * 70)
print(f"Categories : {len(CATEGORIES)}")
print(f"Model      : YOLO11s")
print(f"Image size : {IMAGE_SIZE}")
print(f"Epochs     : {EPOCHS}")
print(f"Batch size : {BATCH_SIZE}")
print(f"Device     : {DEVICE}")
print("=" * 70)

for index, category in enumerate(CATEGORIES, start=1):

    print("\n")
    print("=" * 70)
    print(f"[{index}/15] TRAINING: {category}")
    print("=" * 70)

    category_dir = DATASET_DIR / category
    yaml_path = category_dir / "data.yaml"

    if not yaml_path.exists():
        print(f"ERROR: data.yaml not found:")
        print(yaml_path)
        failed.append(category)
        continue

    try:

        # Fresh pretrained YOLO11s model. The dataset contains only defect
        # images with boxes generated from the corresponding ground-truth
        # masks; GOOD images are intentionally not used as defect labels.
        model = YOLO("yolo11s.pt")

        model.train(
            data=str(yaml_path),

            # Training
            epochs=EPOCHS,
            imgsz=IMAGE_SIZE,
            batch=BATCH_SIZE,
            patience=PATIENCE,

            # CPU
            device=DEVICE,
            workers=2,

            # Optimizer
            optimizer="AdamW",
            lr0=0.0005,
            lrf=0.01,
            weight_decay=0.0005,

            # Small-defect-friendly augmentation
            hsv_h=0.01,
            hsv_s=0.30,
            hsv_v=0.20,

            degrees=5.0,
            translate=0.05,
            scale=0.15,
            shear=2.0,
            perspective=0.0,

            # Avoid destroying tiny defect regions
            flipud=0.0,
            fliplr=0.5,

            # Mosaic can make tiny defects harder to learn
            mosaic=0.10,
            mixup=0.0,
            copy_paste=0.0,

            # Turn mosaic off near end of training
            close_mosaic=20,

            # Validation
            val=True,

            # Save best model
            save=True,
            save_period=-1,

            # Output
            project=str(RUNS_DIR),
            name=f"{category}_defect_final",
            exist_ok=True,

            # Reproducibility
            seed=42,

            # Cache disabled to reduce RAM usage
            cache=False,

            # Verbose output
            verbose=True
        )

        best_model = (
            RUNS_DIR
            / f"{category}_defect_final"
            / "weights"
            / "best.pt"
        )

        if best_model.exists():
            successful.append(category)
            print(f"\nSUCCESS: {category}")
            print(f"Best model: {best_model}")
        else:
            failed.append(category)
            print(f"\nFAILED: best.pt not found for {category}")

    except Exception as e:

        failed.append(category)

        print(f"\nERROR training {category}")
        print(str(e))
        traceback.print_exc()


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(f"\nSuccessful: {len(successful)} / 15")
for category in successful:
    print(f"  ✓ {category}")

print(f"\nFailed: {len(failed)} / 15")
for category in failed:
    print(f"  ✗ {category}")

print("\n")
print("=" * 70)
print("MODELS LOCATION")
print("=" * 70)
print(RUNS_DIR)