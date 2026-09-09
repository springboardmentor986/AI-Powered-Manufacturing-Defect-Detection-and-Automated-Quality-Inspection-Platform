from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from ai.models.anomaly_detector import AnomalyDetector


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = PROJECT_ROOT / "mvtec_anomaly_detection"
NORMAL_FEATURES = (
    PROJECT_ROOT
    / "ai"
    / "models"
    / "normal_features_layer3.pt"
)

RANDOM_SEED = 42
MEMORY_RATIO = 0.8
VALIDATION_DEFECT_RATIO = 0.2


def get_categories():
    return sorted(
        path.name
        for path in DATASET_ROOT.iterdir()
        if path.is_dir()
    )


def get_train_good_images(category):
    path = DATASET_ROOT / category / "train" / "good"
    return sorted(path.glob("*.png"))


def get_defect_images(category):
    test_path = DATASET_ROOT / category / "test"

    images = []

    for defect_type_path in sorted(test_path.iterdir()):
        if not defect_type_path.is_dir():
            continue

        if defect_type_path.name == "good":
            continue

        images.extend(
            sorted(defect_type_path.glob("*.png"))
        )

    return images


def get_mask_path(image_path):
    category_path = image_path.parent.parent.parent
    defect_type = image_path.parent.name

    return (
        category_path
        / "ground_truth"
        / defect_type
        / f"{image_path.stem}_mask.png"
    )


def split_validation_data(category):
    rng = np.random.default_rng(RANDOM_SEED)

    normal_images = get_train_good_images(category)
    defect_images = get_defect_images(category)

    rng.shuffle(normal_images)
    rng.shuffle(defect_images)

    memory_size = int(
        len(normal_images) * MEMORY_RATIO
    )

    validation_normal = normal_images[memory_size:]

    validation_defect_size = int(
        len(defect_images) * VALIDATION_DEFECT_RATIO
    )

    validation_defects = defect_images[
        :validation_defect_size
    ]

    return validation_normal, validation_defects


def build_category_memory(detector, image_paths):
    features = []

    for image_path in image_paths:
        image, _, _ = detector.preprocess(
            str(image_path)
        )

        local_features = detector.extract_features(image)

        features.append(
            local_features[0].cpu()
        )

    return np.concatenate(
        [item.numpy() for item in features],
        axis=0,
    )


def load_ground_truth(mask_path):
    mask = cv2.imread(
        str(mask_path),
        cv2.IMREAD_GRAYSCALE,
    )

    if mask is None:
        raise ValueError(
            f"Could not read mask: {mask_path}"
        )

    return mask > 0


def calculate_metrics(predicted_mask, ground_truth):
    predicted = predicted_mask.astype(bool)
    ground_truth = ground_truth.astype(bool)

    intersection = np.logical_and(
        predicted,
        ground_truth,
    ).sum()

    union = np.logical_or(
        predicted,
        ground_truth,
    ).sum()

    true_positive = intersection

    false_positive = np.logical_and(
        predicted,
        ~ground_truth,
    ).sum()

    false_negative = np.logical_and(
        ~predicted,
        ground_truth,
    ).sum()

    precision_denominator = (
        true_positive + false_positive
    )

    recall_denominator = (
        true_positive + false_negative
    )

    precision = (
        true_positive / precision_denominator
        if precision_denominator > 0
        else 0.0
    )

    recall = (
        true_positive / recall_denominator
        if recall_denominator > 0
        else 0.0
    )

    f1_denominator = precision + recall

    f1 = (
        2 * precision * recall / f1_denominator
        if f1_denominator > 0
        else 0.0
    )

    iou = (
        intersection / union
        if union > 0
        else 0.0
    )

    return precision, recall, f1, iou


def main():
    categories = get_categories()

    detector = AnomalyDetector(
        str(NORMAL_FEATURES)
    )

    results = []

    for category in categories:
        print(f"\nEvaluating {category}")

        validation_normal, validation_defects = (
            split_validation_data(category)
        )

        category_memory = build_category_memory(
            detector,
            validation_normal,
        )

        detector.normal_features = (
            detector.normal_features.new_tensor(
                category_memory
            )
        )

        category_results = []

        for image_path in validation_defects:
            result = detector.predict(
                str(image_path)
            )

            predicted_mask = result[
                "localization_mask"
            ]

            mask_path = get_mask_path(image_path)

            ground_truth = load_ground_truth(
                mask_path
            )

            precision, recall, f1, iou = (
                calculate_metrics(
                    predicted_mask,
                    ground_truth,
                )
            )

            category_results.append(
                {
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "iou": iou,
                }
            )

        results.append(
            {
                "category": category,
                "images": len(category_results),
                "precision": np.mean(
                    [
                        item["precision"]
                        for item in category_results
                    ]
                ),
                "recall": np.mean(
                    [
                        item["recall"]
                        for item in category_results
                    ]
                ),
                "f1": np.mean(
                    [
                        item["f1"]
                        for item in category_results
                    ]
                ),
                "iou": np.mean(
                    [
                        item["iou"]
                        for item in category_results
                    ]
                ),
            }
        )

    results_df = pd.DataFrame(results)

    print("\nValidation localization results:")
    print(
        results_df.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print("\nMacro average:")

    print(
        f"Precision: {results_df['precision'].mean():.4f}"
    )
    print(
        f"Recall:    {results_df['recall'].mean():.4f}"
    )
    print(
        f"F1:        {results_df['f1'].mean():.4f}"
    )
    print(
        f"IoU:       {results_df['iou'].mean():.4f}"
    )

    output_path = (
        PROJECT_ROOT
        / "ai"
        / "evaluation"
        / "localization_validation_results.csv"
    )

    results_df.to_csv(
        output_path,
        index=False,
    )

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()