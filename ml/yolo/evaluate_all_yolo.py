from pathlib import Path
from ultralytics import YOLO
import csv

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"D:\VisionInspectAI\ml")
YOLO_DIR = BASE_DIR / "yolo"

DATASETS_DIR = YOLO_DIR / "all_categories"
RUNS_DIR = YOLO_DIR / "runs"

OUTPUT_CSV = YOLO_DIR / "yolo_all_categories_results.csv"

# All 15 categories
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

# Bottle was trained separately with the improved configuration.
MODEL_RUN_NAMES = {
    "bottle": "bottle_defect_improved"
}

# ============================================================
# RESULTS
# ============================================================

results_table = []

print("=" * 70)
print("VISIONINSPECT AI")
print("YOLO11n EVALUATION - ALL 15 CATEGORIES")
print("=" * 70)


# ============================================================
# EVALUATE EACH CATEGORY
# ============================================================

for index, category in enumerate(CATEGORIES, start=1):

    print("\n" + "=" * 70)
    print(f"[{index}/15] EVALUATING: {category}")
    print("=" * 70)

    data_yaml = DATASETS_DIR / category / "data.yaml"

    # Bottle has its improved model
    if category in MODEL_RUN_NAMES:

        run_name = MODEL_RUN_NAMES[category]

    else:

        run_name = f"{category}_defect"

    model_path = (
        RUNS_DIR /
        run_name /
        "weights" /
        "best.pt"
    )

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not data_yaml.exists():

        print("ERROR: data.yaml not found:")
        print(data_yaml)

        results_table.append({
            "category": category,
            "status": "FAILED",
            "precision": "",
            "recall": "",
            "map50": "",
            "map50_95": ""
        })

        continue

    if not model_path.exists():

        print("ERROR: YOLO model not found:")
        print(model_path)

        results_table.append({
            "category": category,
            "status": "FAILED",
            "precision": "",
            "recall": "",
            "map50": "",
            "map50_95": ""
        })

        continue

    try:

        print("\nModel:")
        print(model_path)

        print("\nLoading model...")

        model = YOLO(str(model_path))

        print("Model loaded successfully.")

        print("\nRunning evaluation on TEST set...")

        results = model.val(
            data=str(data_yaml),
            split="test",
            imgsz=640,
            batch=8,
            plots=True
        )

        precision = float(results.box.mp)
        recall = float(results.box.mr)
        map50 = float(results.box.map50)
        map50_95 = float(results.box.map)

        print("\nRESULTS")
        print("-" * 50)
        print(f"Precision    : {precision:.4f}")
        print(f"Recall       : {recall:.4f}")
        print(f"mAP@0.5      : {map50:.4f}")
        print(f"mAP@0.5:0.95 : {map50_95:.4f}")
        print("-" * 50)

        results_table.append({
            "category": category,
            "status": "SUCCESS",
            "precision": f"{precision:.4f}",
            "recall": f"{recall:.4f}",
            "map50": f"{map50:.4f}",
            "map50_95": f"{map50_95:.4f}"
        })

    except Exception as e:

        print("\nERROR:")
        print(e)

        results_table.append({
            "category": category,
            "status": "FAILED",
            "precision": "",
            "recall": "",
            "map50": "",
            "map50_95": ""
        })


# ============================================================
# SAVE CSV
# ============================================================

with open(
    OUTPUT_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "category",
            "status",
            "precision",
            "recall",
            "map50",
            "map50_95"
        ]
    )

    writer.writeheader()

    writer.writerows(results_table)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("FINAL YOLO EVALUATION SUMMARY")
print("=" * 70)

print(
    f"{'Category':<15}"
    f"{'Precision':<12}"
    f"{'Recall':<12}"
    f"{'mAP50':<12}"
    f"{'mAP50-95':<12}"
)

print("-" * 70)

successful_results = []

for row in results_table:

    if row["status"] == "SUCCESS":

        print(
            f"{row['category']:<15}"
            f"{row['precision']:<12}"
            f"{row['recall']:<12}"
            f"{row['map50']:<12}"
            f"{row['map50_95']:<12}"
        )

        successful_results.append(row)

    else:

        print(
            f"{row['category']:<15}"
            f"{'FAILED':<12}"
        )


print("-" * 70)

print("\nResults saved to:")
print(OUTPUT_CSV)

print("\nEvaluation completed.")
print("=" * 70)