from ultralytics import YOLO
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_YAML = BASE_DIR / "data.yaml"

# ============================================================
# LOAD PRETRAINED YOLO MODEL
# ============================================================

print("=" * 60)
print("Loading pretrained YOLO11n model")
print("=" * 60)

model = YOLO("yolo11n.pt")

print("YOLO model loaded successfully!")

# ============================================================
# TRAIN IMPROVED MODEL
# ============================================================

print("\n" + "=" * 60)
print("Starting improved YOLO training")
print("=" * 60)

results = model.train(
    data=str(DATA_YAML),

    # Training
    epochs=100,
    imgsz=640,
    batch=8,

    # Early stopping
    patience=20,

    # Learning
    optimizer="AdamW",
    lr0=0.001,
    lrf=0.01,
    weight_decay=0.0005,

    # Augmentation
    hsv_h=0.015,
    hsv_s=0.4,
    hsv_v=0.4,

    degrees=5.0,
    translate=0.1,
    scale=0.5,
    shear=2.0,

    fliplr=0.5,
    flipud=0.0,

    mosaic=1.0,
    mixup=0.1,

    # Reproducibility
    seed=42,

    # Save separately
    project=str(BASE_DIR / "runs"),
    name="bottle_defect_improved",

    pretrained=True,
    plots=True,
    save=True
)

# ============================================================
# COMPLETED
# ============================================================

print("\n" + "=" * 60)
print("IMPROVED YOLO TRAINING COMPLETED")
print("=" * 60)

print("Results:")
print(
    BASE_DIR
    / "runs"
    / "bottle_defect_improved"
)

print("\nBest model:")
print(
    BASE_DIR
    / "runs"
    / "bottle_defect_improved"
    / "weights"
    / "best.pt"
)

print("=" * 60)