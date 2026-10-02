from pathlib import Path
from ultralytics import YOLO
import cv2
import shutil

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"D:\VisionInspectAI\ml")

YOLO_DIR = BASE_DIR / "yolo"
DATASETS_DIR = YOLO_DIR / "all_categories"
RUNS_DIR = YOLO_DIR / "runs"

OUTPUT_DIR = BASE_DIR / "runs" / "predictions"

# ============================================================
# ALL 15 CATEGORIES
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
# SETTINGS
# ============================================================

CONFIDENCE = 0.10
IMAGE_SIZE = 640

# ============================================================
# CLEAN OLD PREDICTIONS
# ============================================================

if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# START
# ============================================================

print("=" * 70)
print("VISIONINSPECT AI")
print("YOLO11n - ALL 15 CATEGORY PREDICTION VISUALIZATION")
print("=" * 70)

successful = []
failed = []

# ============================================================
# PREDICT
# ============================================================

for index, category in enumerate(CATEGORIES, start=1):

    print("\n" + "=" * 70)
    print(f"[{index}/15] {category.upper()}")
    print("=" * 70)

    # CORRECT DATASET STRUCTURE
    test_dir = (
        DATASETS_DIR
        / category
        / "images"
        / "test"
    )

    if not test_dir.exists():

        print("TEST IMAGE DIRECTORY NOT FOUND:")
        print(test_dir)

        failed.append(category)
        continue

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model_path = (
        RUNS_DIR
        / f"{category}_defect"
        / "weights"
        / "best.pt"
    )

    if not model_path.exists():

        print("MODEL NOT FOUND:")
        print(model_path)

        failed.append(category)
        continue

    print("Model:")
    print(model_path)

    print("\nTest images:")
    print(test_dir)

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    category_output = OUTPUT_DIR / category

    category_output.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    model = YOLO(str(model_path))

    # --------------------------------------------------------
    # GET TEST IMAGES
    # --------------------------------------------------------

    image_files = sorted(
        list(test_dir.glob("*.png")) +
        list(test_dir.glob("*.jpg")) +
        list(test_dir.glob("*.jpeg"))
    )

    print(f"\nImages found: {len(image_files)}")

    detection_count = 0

    # --------------------------------------------------------
    # RUN PREDICTIONS
    # --------------------------------------------------------

    for image_path in image_files:

        results = model.predict(
            source=str(image_path),
            conf=CONFIDENCE,
            imgsz=IMAGE_SIZE,
            verbose=False
        )

        result = results[0]

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            continue

        boxes = result.boxes

        if boxes is not None and len(boxes) > 0:

            detection_count += len(boxes)

            for box in boxes:

                x1, y1, x2, y2 = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)
                )

                confidence = float(
                    box.conf[0].cpu().numpy()
                )

                cv2.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                label = (
                    f"DEFECT {confidence:.2f}"
                )

                cv2.putText(
                    image,
                    label,
                    (x1, max(25, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

        else:

            cv2.putText(
                image,
                "NO DEFECT DETECTED",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )

        output_path = (
            category_output
            / image_path.name
        )

        cv2.imwrite(
            str(output_path),
            image
        )

    print(f"Detections: {detection_count}")

    successful.append(category)

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("ALL 15 YOLO PREDICTIONS COMPLETED")
print("=" * 70)

print("\nSuccessful:")

for category in successful:
    print(f"  [OK] {category}")

print("\nFailed:")

if failed:

    for category in failed:
        print(f"  [FAILED] {category}")

else:

    print("  None")

print("\n" + "-" * 70)

print(f"Successful: {len(successful)} / 15")
print(f"Failed:     {len(failed)} / 15")

print("\nPrediction images saved to:")
print(OUTPUT_DIR)

print("=" * 70)