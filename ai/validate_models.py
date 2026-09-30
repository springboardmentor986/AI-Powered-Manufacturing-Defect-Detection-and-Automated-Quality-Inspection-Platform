from pathlib import Path

import cv2
import joblib
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


BASE_DIR = Path("datasets/mvtec_ad")
MODEL_DIR = Path("ai/models")

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


def extract_features(image_path):
    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"Unable to read: {image_path}")

    image = cv2.resize(image, (128, 128))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0,
    )

    enhanced = cv2.equalizeHist(blurred)

    edges = cv2.Canny(
        enhanced,
        50,
        150,
    )

    enhanced_small = cv2.resize(
        enhanced,
        (32, 32),
    )

    edges_small = cv2.resize(
        edges,
        (32, 32),
    )

    enhanced_features = (
        enhanced_small.astype(np.float32) / 255.0
    )

    edge_features = (
        edges_small.astype(np.float32) / 255.0
    )

    return np.concatenate([
        enhanced_features.flatten(),
        edge_features.flatten(),
    ])


def validate_category(category):

    model_path = (
        MODEL_DIR
        / category
        / "model_package.joblib"
    )

    test_dir = (
        BASE_DIR
        / category
        / "test"
    )

    package = joblib.load(model_path)

    model = package["model"]
    threshold = float(package["threshold"])

    y_true = []
    y_pred = []

    good_count = 0
    defective_count = 0

    for defect_dir in sorted(test_dir.iterdir()):

        if not defect_dir.is_dir():
            continue

        actual_defective = (
            defect_dir.name != "good"
        )

        for image_path in sorted(
            defect_dir.iterdir()
        ):

            if image_path.suffix.lower() not in [
                ".png",
                ".jpg",
                ".jpeg",
            ]:
                continue

            try:
                features = extract_features(
                    image_path
                )

                score = float(
                    model.decision_function(
                        features.reshape(1, -1)
                    )[0]
                )

                predicted_defective = (
                    score < threshold
                )

                y_true.append(
                    int(actual_defective)
                )

                y_pred.append(
                    int(predicted_defective)
                )

                if actual_defective:
                    defective_count += 1
                else:
                    good_count += 1

            except Exception as error:

                print(
                    f"Skipping {image_path}: {error}"
                )

    if not y_true:
        return None

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    tn, fp, fn, tp = matrix.ravel()

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    false_negative_rate = (
        fn / (fn + tp)
        if (fn + tp) > 0
        else 0.0
    )

    return {
        "category": category,
        "threshold": threshold,
        "good_images": good_count,
        "defective_images": defective_count,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def main():

    print("=" * 80)
    print("VISIONINSPECT AI - MVTec AD MODEL VALIDATION")
    print("=" * 80)

    results = []

    for category in CATEGORIES:

        print(
            f"\nValidating: {category}"
        )

        try:

            result = validate_category(
                category
            )

            if result:
                results.append(result)

                print(
                    f"  Accuracy : "
                    f"{result['accuracy']:.4f}"
                )

                print(
                    f"  Precision: "
                    f"{result['precision']:.4f}"
                )

                print(
                    f"  Recall   : "
                    f"{result['recall']:.4f}"
                )

                print(
                    f"  F1       : "
                    f"{result['f1']:.4f}"
                )

                print(
                    f"  FPR      : "
                    f"{result['false_positive_rate']:.4f}"
                )

                print(
                    f"  FNR      : "
                    f"{result['false_negative_rate']:.4f}"
                )

        except Exception as error:

            print(
                f"  ERROR: {error}"
            )

    print("\n")
    print("=" * 80)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 80)

    print(
        f"{'Category':<15}"
        f"{'Accuracy':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
        f"{'FNR':<12}"
    )

    print("-" * 80)

    for result in results:

        print(
            f"{result['category']:<15}"
            f"{result['accuracy']:<12.4f}"
            f"{result['precision']:<12.4f}"
            f"{result['recall']:<12.4f}"
            f"{result['f1']:<12.4f}"
            f"{result['false_negative_rate']:<12.4f}"
        )

    if results:

        macro_accuracy = np.mean([
            r["accuracy"]
            for r in results
        ])

        macro_precision = np.mean([
            r["precision"]
            for r in results
        ])

        macro_recall = np.mean([
            r["recall"]
            for r in results
        ])

        macro_f1 = np.mean([
            r["f1"]
            for r in results
        ])

        print("-" * 80)

        print(
            f"{'MACRO AVG':<15}"
            f"{macro_accuracy:<12.4f}"
            f"{macro_precision:<12.4f}"
            f"{macro_recall:<12.4f}"
            f"{macro_f1:<12.4f}"
        )

    print("\nValidation complete.")


if __name__ == "__main__":
    main()