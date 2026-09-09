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
            local_features[0].cpu().numpy()
        )

    return np.concatenate(
        features,
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


def get_max_patch_center(anomaly_map, height, width):
    row, col = np.unravel_index(
        np.argmax(anomaly_map),
        anomaly_map.shape,
    )

    patch_height = height / anomaly_map.shape[0]
    patch_width = width / anomaly_map.shape[1]

    center_y = int(
        (row + 0.5) * patch_height
    )

    center_x = int(
        (col + 0.5) * patch_width
    )

    center_y = min(
        center_y,
        height - 1,
    )

    center_x = min(
        center_x,
        width - 1,
    )

    return center_x, center_y


def main():
    detector = AnomalyDetector(
        str(NORMAL_FEATURES)
    )

    results = []

    for category in get_categories():
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

        localized = 0

        for image_path in validation_defects:
            result = detector.predict(
                str(image_path)
            )

            anomaly_map = result["anomaly_map"]

            height = result["original_height"]
            width = result["original_width"]

            center_x, center_y = get_max_patch_center(
                anomaly_map,
                height,
                width,
            )

            ground_truth = load_ground_truth(
                get_mask_path(image_path)
            )

            if ground_truth[center_y, center_x]:
                localized += 1

        total = len(validation_defects)

        accuracy = (
            localized / total
            if total > 0
            else 0.0
        )

        results.append(
            {
                "category": category,
                "images": total,
                "localized": localized,
                "point_localization_accuracy": accuracy,
            }
        )

    results_df = pd.DataFrame(results)

    print("\nPoint localization results:")

    print(
        results_df.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print(
        f"\nMacro point localization accuracy: "
        f"{results_df['point_localization_accuracy'].mean():.4f}"
    )

    output_path = (
        PROJECT_ROOT
        / "ai"
        / "evaluation"
        / "point_localization_results.csv"
    )

    results_df.to_csv(
        output_path,
        index=False,
    )

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()