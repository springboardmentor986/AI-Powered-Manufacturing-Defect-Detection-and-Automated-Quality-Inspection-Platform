
import os
import random
import json
import time
import torch
import numpy as np

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features

DATASET_PATH = r"C:\Users\chand\Downloads\mvtec_anomaly_detection"
OUTPUT_PATH = "ml4_evaluation_results_80.json"

CATEGORIES = [
    "bottle", "cable", "capsule", "carpet", "grid",
    "hazelnut", "leather", "metal_nut", "pill", "screw",
    "tile", "toothbrush", "transistor", "wood", "zipper"
]

RANDOM_SEED = 42
VALIDATION_RATIO = 0.20
NORMAL_QUANTILE = 0.80


def image_files(folder):
    if not os.path.isdir(folder):
        return []

    return sorted(
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if name.lower().endswith((".png", ".jpg", ".jpeg"))
    )


def extract_image_features(path):
    with open(path, "rb") as file:
        image_bytes = file.read()

    image = preprocess_image(image_bytes)
    features = extract_features(image)

    return features.detach().cpu().reshape(-1)


def get_score(path, normal_center):
    features = extract_image_features(path)
    return float(torch.norm(features - normal_center).item())


def evaluate_category(category):
    print(f"\nEvaluating {category}...")

    train_good = image_files(
        os.path.join(DATASET_PATH, category, "train", "good")
    )

    test_root = os.path.join(DATASET_PATH, category, "test")

    if not train_good or not os.path.isdir(test_root):
        print("SKIPPED: missing training-good or test folder")
        return None

    shuffled = train_good.copy()
    random.Random(RANDOM_SEED).shuffle(shuffled)

    validation_count = max(
        1, int(len(shuffled) * VALIDATION_RATIO)
    )

    validation_images = shuffled[:validation_count]
    reference_images = shuffled[validation_count:]

    if not reference_images:
        print("SKIPPED: insufficient reference images")
        return None

    start = time.perf_counter()

    reference_features = torch.stack([
        extract_image_features(path)
        for path in reference_images
    ])

    normal_center = reference_features.mean(dim=0)

    validation_scores = [
        get_score(path, normal_center)
        for path in validation_images
    ]

    threshold = float(
        np.quantile(validation_scores, NORMAL_QUANTILE)
    )

    good_test = image_files(
        os.path.join(test_root, "good")
    )

    defect_test = []

    for folder_name in sorted(os.listdir(test_root)):
        if folder_name == "good":
            continue

        folder_path = os.path.join(test_root, folder_name)

        if os.path.isdir(folder_path):
            defect_test.extend(image_files(folder_path))

    tp = tn = fp = fn = 0

    for path in good_test:
        score = get_score(path, normal_center)

        if score > threshold:
            fp += 1
        else:
            tn += 1

    for path in defect_test:
        score = get_score(path, normal_center)

        if score > threshold:
            tp += 1
        else:
            fn += 1

    total = tp + tn + fp + fn

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    accuracy = (tp + tn) / total if total else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    elapsed = time.perf_counter() - start

    threshold_rule = (
        "80th percentile of held-out normal training scores"
    )

    result = {
        "category": category,
        "threshold_rule": threshold_rule,
        "threshold": round(threshold, 6),
        "reference_normal_images": len(reference_images),
        "validation_normal_images": len(validation_images),
        "test_good_images": len(good_test),
        "test_defect_images": len(defect_test),
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": round(accuracy, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "evaluation_seconds": round(elapsed, 2),
    }

    print(
        f"Threshold={threshold:.4f} | "
        f"Accuracy={accuracy * 100:.2f}% | "
        f"Precision={precision * 100:.2f}% | "
        f"Recall={recall * 100:.2f}% | "
        f"F1={f1 * 100:.2f}%"
    )

    return result


def main():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    torch.manual_seed(RANDOM_SEED)

    print("=" * 60)
    print("VisionInspect AI - ML4 Independent Evaluation")
    print("Threshold selection uses normal validation images only")
    print(f"Threshold percentile: {NORMAL_QUANTILE * 100:.0f}%")
    print("=" * 60)

    results = []

    for category in CATEGORIES:
        result = evaluate_category(category)

        if result is not None:
            results.append(result)

    if not results:
        raise RuntimeError("No categories were evaluated.")

    tp = sum(item["TP"] for item in results)
    tn = sum(item["TN"] for item in results)
    fp = sum(item["FP"] for item in results)
    fn = sum(item["FN"] for item in results)

    total = tp + tn + fp + fn

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    accuracy = (tp + tn) / total if total else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    report = {
        "evaluation": "ML4 independent threshold evaluation",
        "threshold_rule": (
            "80th percentile of held-out normal training scores"
        ),
        "categories_evaluated": len(results),
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": round(accuracy, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "category_results": results,
        "caution": (
            "The threshold is estimated from held-out normal training "
            "images only. This does not guarantee optimal defect detection. "
            "The official test set is used for evaluation, not threshold "
            "selection."
        ),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("\n" + "=" * 60)
    print(f"Categories evaluated: {len(results)}/{len(CATEGORIES)}")
    print(f"TP={tp} TN={tn} FP={fp} FN={fn}")
    print(f"Accuracy : {accuracy * 100:.2f}%")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall   : {recall * 100:.2f}%")
    print(f"F1-score : {f1 * 100:.2f}%")
    print(f"Saved report: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()