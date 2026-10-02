from pathlib import Path
from ultralytics import YOLO

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"D:\VisionInspectAI\ml")
YOLO_DIR = BASE_DIR / "yolo"

DATASETS_DIR = YOLO_DIR / "all_categories"
RUNS_DIR = YOLO_DIR / "runs"

CATEGORIES = [
    "toothbrush",
    "transistor",
    "screw"
]

# ============================================================
# EVALUATION
# ============================================================

print("=" * 70)
print("VISIONINSPECT AI")
print("RETRAINED YOLO11n - EVALUATION")
print("=" * 70)

for index, category in enumerate(CATEGORIES, start=1):

    print("\n" + "=" * 70)
    print(f"[{index}/3] EVALUATING: {category.upper()}")
    print("=" * 70)

    model_path = (
        RUNS_DIR
        / f"{category}_defect_retrained"
        / "weights"
        / "best.pt"
    )

    data_yaml = (
        DATASETS_DIR
        / category
        / "data.yaml"
    )

    if not model_path.exists():
        print("MODEL NOT FOUND:")
        print(model_path)
        continue

    if not data_yaml.exists():
        print("DATA YAML NOT FOUND:")
        print(data_yaml)
        continue

    print("\nModel:")
    print(model_path)

    print("\nLoading model...")

    model = YOLO(str(model_path))

    print("Model loaded successfully.")

    print("\nEvaluating TEST dataset...")

    results = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=800,
        batch=4,
        plots=True
    )

    precision = float(results.box.mp)
    recall = float(results.box.mr)
    map50 = float(results.box.map50)
    map50_95 = float(results.box.map)

    print("\n" + "-" * 60)
    print(f"{category.upper()} RESULTS")
    print("-" * 60)

    print(f"Precision    : {precision:.4f}")
    print(f"Recall       : {recall:.4f}")
    print(f"mAP@0.5      : {map50:.4f}")
    print(f"mAP@0.5:0.95 : {map50_95:.4f}")

    print("-" * 60)


print("\n")
print("=" * 70)
print("RETRAINED MODEL EVALUATION COMPLETED")
print("=" * 70)