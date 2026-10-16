
import os
import json
import torch
import numpy as np

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features

DATASET_PATH = r"C:\Users\chand\Downloads\mvtec_anomaly_detection"
FEATURES_PATH = "normal_features.pt"
THRESHOLDS_PATH = "live_thresholds_calibrated.json"
OUTPUT_PATH = "ml4_calibrated_evaluation.json"

normal_features = torch.load(
    FEATURES_PATH,
    map_location="cpu",
    weights_only=False
)

with open(THRESHOLDS_PATH, "r", encoding="utf-8") as f:
    thresholds = json.load(f)


def get_image_files(folder):
    if not os.path.isdir(folder):
        return []

    return sorted(
        name for name in os.listdir(folder)
        if name.lower().endswith((".png", ".jpg", ".jpeg"))
    )


def extract_image_features(path):
    with open(path, "rb") as f:
        image_bytes = f.read()

    image = preprocess_image(image_bytes)

    return extract_features(image).detach().cpu().reshape(-1)


total_tp = 0
total_tn = 0
total_fp = 0
total_fn = 0
category_results = {}

for category, reference_features in normal_features.items():
    print(f"\nEvaluating {category}...")

    if category not in thresholds:
        raise RuntimeError(f"Missing threshold for {category}")

    test_path = os.path.join(
        DATASET_PATH, category, "test"
    )

    if not os.path.isdir(test_path):
        raise RuntimeError(f"Test folder not found: {test_path}")

    threshold = float(thresholds[category])
    normal_center = reference_features.mean(dim=0).reshape(-1)

    tp = tn = fp = fn = 0

    for defect_type in sorted(os.listdir(test_path)):
        defect_path = os.path.join(test_path, defect_type)

        if not os.path.isdir(defect_path):
            continue

        actual_defect = defect_type != "good"

        for filename in get_image_files(defect_path):
            image_path = os.path.join(defect_path, filename)

            features = extract_image_features(image_path)
            score = float(
                torch.norm(features - normal_center).item()
            )

            predicted_defect = score > threshold

            if actual_defect and predicted_defect:
                tp += 1
            elif not actual_defect and not predicted_defect:
                tn += 1
            elif not actual_defect and predicted_defect:
                fp += 1
            else:
                fn += 1

    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) else 0.0
    )

    category_results[category] = {
        "threshold": threshold,
        "test_images": total,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy_percent": round(accuracy * 100, 2),
        "precision_percent": round(precision * 100, 2),
        "recall_percent": round(recall * 100, 2),
        "f1_percent": round(f1 * 100, 2)
    }

    total_tp += tp
    total_tn += tn
    total_fp += fp
    total_fn += fn

    print(
        f"Images: {total} | "
        f"Accuracy: {accuracy * 100:.2f}% | "
        f"Precision: {precision * 100:.2f}% | "
        f"Recall: {recall * 100:.2f}% | "
        f"F1: {f1 * 100:.2f}%"
    )

total = total_tp + total_tn + total_fp + total_fn

accuracy = (
    (total_tp + total_tn) / total if total else 0.0
)
precision = (
    total_tp / (total_tp + total_fp)
    if (total_tp + total_fp) else 0.0
)
recall = (
    total_tp / (total_tp + total_fn)
    if (total_tp + total_fn) else 0.0
)
f1 = (
    2 * precision * recall / (precision + recall)
    if (precision + recall) else 0.0
)

report = {
    "evaluation": "Calibrated live thresholds",
    "threshold_quantile": 0.80,
    "categories_evaluated": len(category_results),
    "total_test_images": total,
    "TP": total_tp,
    "TN": total_tn,
    "FP": total_fp,
    "FN": total_fn,
    "accuracy_percent": round(accuracy * 100, 2),
    "precision_percent": round(precision * 100, 2),
    "recall_percent": round(recall * 100, 2),
    "f1_percent": round(f1 * 100, 2),
    "per_category": category_results
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("\n" + "=" * 45)
print("CALIBRATED THRESHOLD EVALUATION")
print("=" * 45)
print(f"Categories: {len(category_results)}")
print(f"Test images: {total}")
print(f"TP: {total_tp} | TN: {total_tn}")
print(f"FP: {total_fp} | FN: {total_fn}")
print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"Precision: {precision * 100:.2f}%")
print(f"Recall:    {recall * 100:.2f}%")
print(f"F1-score:  {f1 * 100:.2f}%")
print(f"\nReport saved to {OUTPUT_PATH}")

if len(category_results) != 15:
    print("WARNING: Expected results for all 15 categories.")