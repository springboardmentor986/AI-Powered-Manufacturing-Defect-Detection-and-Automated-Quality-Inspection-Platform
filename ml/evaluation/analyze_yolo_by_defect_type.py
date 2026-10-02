import os
from collections import defaultdict

from ultralytics import YOLO


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
YOLO_RUNS_DIR = os.path.join(BASE_DIR, "yolo", "runs")

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
    "zipper",
]


def find_model(category):

    retrained = {
        "screw",
        "toothbrush",
        "transistor"
    }

    if category in retrained:
        path = os.path.join(
            YOLO_RUNS_DIR,
            f"{category}_defect_retrained",
            "weights",
            "best.pt"
        )
    else:
        path = os.path.join(
            YOLO_RUNS_DIR,
            f"{category}_defect",
            "weights",
            "best.pt"
        )

    return path if os.path.exists(path) else None


def get_defect_images(category):

    test_dir = os.path.join(
        DATASET_DIR,
        category,
        "test"
    )

    data = []

    if not os.path.exists(test_dir):
        return data

    for defect_type in sorted(os.listdir(test_dir)):

        if defect_type == "good":
            continue

        defect_dir = os.path.join(
            test_dir,
            defect_type
        )

        if not os.path.isdir(defect_dir):
            continue

        for filename in sorted(os.listdir(defect_dir)):

            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp")
            ):

                data.append(
                    (
                        os.path.join(defect_dir, filename),
                        defect_type
                    )
                )

    return data


def analyze_category(category):

    print()
    print("=" * 70)
    print(category.upper())
    print("=" * 70)

    model_path = find_model(category)

    if model_path is None:
        print("YOLO model not found.")
        return

    model = YOLO(model_path)

    images = get_defect_images(category)

    stats = defaultdict(
        lambda: {
            "total": 0,
            "detected": 0,
            "missed": 0
        }
    )

    for image_path, defect_type in images:

        stats[defect_type]["total"] += 1

        results = model.predict(
            source=image_path,
            conf=0.05,
            imgsz=800,
            iou=0.45,
            max_det=20,
            verbose=False
        )

        detection_count = 0

        for result in results:

            if result.boxes is not None:
                detection_count += len(result.boxes)

        if detection_count > 0:
            stats[defect_type]["detected"] += 1
        else:
            stats[defect_type]["missed"] += 1

    print()

    print(
        f"{'Defect Type':<25}"
        f"{'Total':<10}"
        f"{'Detected':<12}"
        f"{'Missed':<10}"
        f"{'Rate':<10}"
    )

    print("-" * 70)

    for defect_type, result in stats.items():

        total = result["total"]
        detected = result["detected"]

        rate = (
            detected / total * 100
            if total > 0
            else 0
        )

        print(
            f"{defect_type:<25}"
            f"{total:<10}"
            f"{detected:<12}"
            f"{result['missed']:<10}"
            f"{rate:.2f}%"
        )


def main():

    print("=" * 80)
    print("VISIONINSPECT AI")
    print("YOLO DETECTION BY DEFECT TYPE")
    print("=" * 80)

    for category in CATEGORIES:

        try:
            analyze_category(category)

        except Exception as e:

            print(
                f"ERROR - {category}: {e}"
            )

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()