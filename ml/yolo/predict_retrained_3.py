from pathlib import Path
from ultralytics import YOLO
import shutil

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"D:\VisionInspectAI\ml")

YOLO_DIR = BASE_DIR / "yolo"
DATASETS_DIR = YOLO_DIR / "all_categories"
RUNS_DIR = YOLO_DIR / "runs"

OUTPUT_DIR = BASE_DIR / "runs" / "predictions_retrained"

CATEGORIES = [
    "toothbrush",
    "transistor",
    "screw"
]

# ============================================================
# SETTINGS
# ============================================================

CONFIDENCE = 0.03
IMAGE_SIZE = 800

# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("VISIONINSPECT AI")
print("RETRAINED YOLO11n - BOUNDING BOX VISUALIZATION")
print("=" * 70)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

for index, category in enumerate(CATEGORIES, start=1):

    print("\n" + "=" * 70)
    print(f"[{index}/3] PREDICTING: {category.upper()}")
    print("=" * 70)

    # --------------------------------------------------------
    # Retrained model
    # --------------------------------------------------------

    model_path = (
        RUNS_DIR
        / f"{category}_defect_retrained"
        / "weights"
        / "best.pt"
    )

    # --------------------------------------------------------
    # Test images
    # --------------------------------------------------------

    test_images = (
        DATASETS_DIR
        / category
        / "test"
        / "images"
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    category_output = OUTPUT_DIR / category

    if category_output.exists():
        shutil.rmtree(category_output)

    category_output.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    if not model_path.exists():

        print("MODEL NOT FOUND:")
        print(model_path)
        continue

    # --------------------------------------------------------
    # Check test images
    # --------------------------------------------------------

    if not test_images.exists():

        print("TEST IMAGES NOT FOUND:")
        print(test_images)
        continue

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading retrained model...")

    model = YOLO(str(model_path))

    print("Model loaded successfully.")

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    print("\nRunning predictions...")
    print(f"Confidence threshold: {CONFIDENCE}")

    results = model.predict(
        source=str(test_images),

        imgsz=IMAGE_SIZE,

        conf=CONFIDENCE,

        save=True,
        save_txt=True,
        save_conf=True,

        project=str(OUTPUT_DIR),
        name=category,

        exist_ok=True,

        verbose=False
    )

    # --------------------------------------------------------
    # Count detections
    # --------------------------------------------------------

    total_detections = 0

    for result in results:

        if result.boxes is not None:
            total_detections += len(result.boxes)

    print("\nPrediction completed.")
    print(f"Images processed: {len(results)}")
    print(f"Total detections: {total_detections}")

    print("\nBounding-box images saved to:")
    print(category_output)


# ============================================================
# FINAL
# ============================================================

print("\n")
print("=" * 70)
print("RETRAINED YOLO VISUALIZATION COMPLETED")
print("=" * 70)

print("\nOpen:")
print(OUTPUT_DIR)

print("\nFolders:")
print("  toothbrush")
print("  transistor")
print("  screw")

print("=" * 70)