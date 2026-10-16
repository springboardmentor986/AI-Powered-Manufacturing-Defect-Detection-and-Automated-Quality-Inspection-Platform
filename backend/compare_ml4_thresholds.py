
import os
import json
import torch

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features

DATASET_PATH = r"C:\Users\chand\Downloads\mvtec_anomaly_detection"
FEATURES_PATH = "normal_features.pt"
CALIBRATED_PATH = "live_thresholds_calibrated.json"
OUTPUT_PATH = "ml4_threshold_comparison.json"

HARDCODED = {
    "bottle": 1.1508,
    "cable": 1.8222,
    "capsule": 0.9139,
    "carpet": 0.6511,
    "grid": 1.0459,
    "hazelnut": 2.3201,
    "leather": 0.7306,
    "metal_nut": 1.8214,
    "pill": 1.0704,
    "screw": 1.6943,
    "tile": 1.2502,
    "toothbrush": 1.6475,
    "transistor": 1.7346,
    "wood": 1.3598,
    "zipper": 1.4081,
}


def image_files(folder):
    if not os.path.isdir(folder):
        return []

    return sorted(
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if name.lower().endswith((".png", ".jpg", ".jpeg"))
    )


def calculate_metrics(counts):
    tp, tn, fp, fn = counts
    total = tp + tn + fp + fn

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    accuracy = (tp + tn) / total if total else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return {
        "test_images": total,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy_percent": round(accuracy * 100, 2),
        "precision_percent": round(precision * 100, 2),
        "recall_percent": round(recall * 100, 2),
        "f1_percent": round(f1 * 100, 2),
    }


def main():
    if os.path.exists(OUTPUT_PATH):
        raise FileExistsError(
            f"{OUTPUT_PATH} already exists. "
            "The script will not overwrite it."
        )

    normal_features = torch.load(
        FEATURES_PATH,
        map_location="cpu",
        weights_only=False,
    )

    with open(CALIBRATED_PATH, "r", encoding="utf-8") as file:
        calibrated = json.load(file)

    categories = sorted(HARDCODED)

    if set(normal_features) != set(categories):
        raise RuntimeError(
            "Normal feature database does not match all 15 categories."
        )

    if set(calibrated) != set(categories):
        raise RuntimeError(
            "Calibrated thresholds do not match all 15 categories."
        )

    threshold_sets = {
        "hardcoded": HARDCODED,
        "calibrated": calibrated,
    }

    totals = {
        name: [0, 0, 0, 0]
        for name in threshold_sets
    }

    per_category = {}

    for category in categories:
        print(f"\nEvaluating {category}...")

        test_root = os.path.join(
            DATASET_PATH, category, "test"
        )

        if not os.path.isdir(test_root):
            raise FileNotFoundError(
                f"Test folder not found: {test_root}"
            )

        center = normal_features[category].mean(dim=0).reshape(-1)

        category_counts = {
            name: [0, 0, 0, 0]
            for name in threshold_sets
        }

        for folder_name in sorted(os.listdir(test_root)):
            folder_path = os.path.join(test_root, folder_name)

            if not os.path.isdir(folder_path):
                continue

            actual_defect = folder_name != "good"

            for path in image_files(folder_path):
                with open(path, "rb") as file:
                    image_bytes = file.read()

                image = preprocess_image(image_bytes)
                features = extract_features(image)
                features = features.detach().cpu().reshape(-1)

                score = float(torch.norm(features - center).item())

                for name, thresholds in threshold_sets.items():
                    predicted_defect = (
                        score > float(thresholds[category])
                    )

                    if actual_defect and predicted_defect:
                        index = 0  # True positive
                    elif not actual_defect and not predicted_defect:
                        index = 1  # True negative
                    elif not actual_defect and predicted_defect:
                        index = 2  # False positive
                    else:
                        index = 3  # False negative

                    category_counts[name][index] += 1
                    totals[name][index] += 1

        per_category[category] = {}

        for name, counts in category_counts.items():
            result = calculate_metrics(counts)
            per_category[category][name] = result

            print(
                f"  {name}: "
                f"Accuracy={result['accuracy_percent']}% | "
                f"Recall={result['recall_percent']}% | "
                f"F1={result['f1_percent']}%"
            )

    report = {
        "evaluation": "Hardcoded versus calibrated thresholds",
        "categories_evaluated": len(categories),
        "method": (
            "Both threshold sets use the same saved normal-feature "
            "center and the same test images. Scores greater than "
            "the category threshold are classified as DEFECT."
        ),
        "overall": {
            name: calculate_metrics(counts)
            for name, counts in totals.items()
        },
        "per_category": per_category,
    }

    with open(OUTPUT_PATH, "x", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\n========== OVERALL COMPARISON ==========")

    for name, result in report["overall"].items():
        print(f"\n{name.upper()}")
        print(f"Accuracy:  {result['accuracy_percent']}%")
        print(f"Precision: {result['precision_percent']}%")
        print(f"Recall:    {result['recall_percent']}%")
        print(f"F1-score:  {result['f1_percent']}%")
        print(f"False positives: {result['FP']}")
        print(f"False negatives: {result['FN']}")

    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
