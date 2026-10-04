"""Evaluate VisionInspect labels against the bundled MVTec test folders.

Usage:
    python evaluate_model.py
    python evaluate_model.py --dataset-assisted
"""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import cv2

from anomaly_detector import detect_defects
from defect_model import PRODUCT_CATEGORY, build_model, load_samples, predict

LABELS = ["good", "contamination", "broken_small", "broken_large"]


def expected_label(category, folder):
    if folder == "good":
        return "good"
    if folder in {"contamination", "metal_contamination", "glue", "thread"}:
        return "contamination"
    if folder in {"broken_large", "broken"}:
        return "broken_large"
    return "broken_small"


def scores(expected, predicted):
    total = len(expected)
    correct = sum(actual == guess for actual, guess in zip(expected, predicted))
    per_class = {}
    for label in LABELS:
        true_positive = sum(actual == label and guess == label for actual, guess in zip(expected, predicted))
        false_positive = sum(actual != label and guess == label for actual, guess in zip(expected, predicted))
        false_negative = sum(actual == label and guess != label for actual, guess in zip(expected, predicted))
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round((2 * precision * recall / (precision + recall)) if precision + recall else 0, 4),
            "support": sum(actual == label for actual in expected),
        }
    binary_expected = [label != "good" for label in expected]
    binary_predicted = [label != "good" for label in predicted]
    binary_correct = sum(actual == guess for actual, guess in zip(binary_expected, binary_predicted))
    true_positive = sum(actual and guess for actual, guess in zip(binary_expected, binary_predicted))
    false_positive = sum(not actual and guess for actual, guess in zip(binary_expected, binary_predicted))
    false_negative = sum(actual and not guess for actual, guess in zip(binary_expected, binary_predicted))
    binary_precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
    binary_recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
    return {
        "samples": total,
        "accuracy": round(correct / total, 4) if total else 0,
        "binary_good_bad": {
            "accuracy": round(binary_correct / total, 4) if total else 0,
            "bad_precision": round(binary_precision, 4),
            "bad_recall": round(binary_recall, 4),
            "bad_f1": round((2 * binary_precision * binary_recall / (binary_precision + binary_recall)) if binary_precision + binary_recall else 0, 4),
        },
        "per_class": per_class,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-assisted", action="store_true", help="Use bundled-image matching used by the demo API")
    parser.add_argument("--limit-per-class", type=int, default=0, help="Evaluate only the first N images in each defect folder")
    parser.add_argument("--holdout", action="store_true", help="Train on 80 percent per label and evaluate the unseen 20 percent")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent / "data" / "mvtec_ad"
    expected, predicted = [], []
    confusion = defaultdict(Counter)
    categories = Counter()

    if args.holdout:
        grouped = defaultdict(list)
        for sample in load_samples(root):
            grouped[sample["label"]].append(sample)
        training, validation = [], []
        for label, samples in grouped.items():
            shuffled = list(samples)
            random.Random(42 + len(label)).shuffle(shuffled)
            split_at = max(1, int(len(shuffled) * 0.8))
            training.extend(shuffled[:split_at])
            validation.extend(shuffled[split_at:])
        model = build_model(training)
        for sample in validation:
            image = cv2.imread(sample["path"], cv2.IMREAD_COLOR)
            result = predict(image, model, category=Path(sample["path"]).parents[2].name)
            expected.append(sample["label"])
            predicted.append(result["label"])
            confusion[sample["label"]][result["label"]] += 1
            categories[Path(sample["path"]).parents[1].name] += 1
        print(json.dumps({
            "mode": "stratified-holdout",
            "training_samples": len(training),
            "validation_samples": len(validation),
            "metrics": scores(expected, predicted),
            "confusion_matrix": {label: dict(confusion[label]) for label in LABELS},
        }, indent=2))
        return

    for category_dir in [root / PRODUCT_CATEGORY]:
        test_dir = category_dir / "test"
        if not test_dir.exists():
            continue
        for defect_dir in sorted(test_dir.iterdir()):
            if not defect_dir.is_dir():
                continue
            image_paths = sorted(defect_dir.iterdir())
            if args.limit_per_class:
                image_paths = image_paths[:args.limit_per_class]
            for image_path in image_paths:
                if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
                    continue
                image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
                if image is None:
                    continue
                actual = expected_label(category_dir.name, defect_dir.name)
                result = detect_defects(image, use_dataset_match=args.dataset_assisted)
                guess = result["defect_type"] if result["classification"] == "bad" else "good"
                expected.append(actual)
                predicted.append(guess)
                confusion[actual][guess] += 1
                categories[category_dir.name] += 1

    report = {
        "mode": "dataset-assisted" if args.dataset_assisted else "image-only",
        "categories": dict(categories),
        "metrics": scores(expected, predicted),
        "confusion_matrix": {label: dict(confusion[label]) for label in LABELS},
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
