from pathlib import Path

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

        local_features = detector.extract_features(
            image
        )

        features.append(
            local_features[0].cpu().numpy()
        )

    return np.concatenate(
        features,
        axis=0,
    )


def calculate_statistics(scores):
    scores = np.array(scores)

    return {
        "count": len(scores),
        "min": scores.min(),
        "mean": scores.mean(),
        "median": np.median(scores),
        "max": scores.max(),
        "std": scores.std(),
    }


def main():
    detector = AnomalyDetector(
        str(NORMAL_FEATURES)
    )

    results = []
    score_records = []

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

        normal_scores = []

        for image_path in validation_normal:
            result = detector.predict(
                str(image_path)
            )

            score = result["anomaly_score"]

            normal_scores.append(score)

            score_records.append(
                {
                    "category": category,
                    "label": "normal",
                    "score": score,
                }
            )

        defect_scores = []

        for image_path in validation_defects:
            result = detector.predict(
                str(image_path)
            )

            score = result["anomaly_score"]

            defect_scores.append(score)

            score_records.append(
                {
                    "category": category,
                    "label": "defective",
                    "score": score,
                }
            )

        normal_stats = calculate_statistics(
            normal_scores
        )

        defect_stats = calculate_statistics(
            defect_scores
        )

        results.append(
            {
                "category": category,

                "normal_count": normal_stats["count"],
                "normal_min": normal_stats["min"],
                "normal_mean": normal_stats["mean"],
                "normal_median": normal_stats["median"],
                "normal_max": normal_stats["max"],
                "normal_std": normal_stats["std"],

                "defect_count": defect_stats["count"],
                "defect_min": defect_stats["min"],
                "defect_mean": defect_stats["mean"],
                "defect_median": defect_stats["median"],
                "defect_max": defect_stats["max"],
                "defect_std": defect_stats["std"],
            }
        )

        print(
            f"Normal   : "
            f"count={normal_stats['count']} "
            f"min={normal_stats['min']:.4f} "
            f"mean={normal_stats['mean']:.4f} "
            f"median={normal_stats['median']:.4f} "
            f"max={normal_stats['max']:.4f}"
        )

        print(
            f"Defective: "
            f"count={defect_stats['count']} "
            f"min={defect_stats['min']:.4f} "
            f"mean={defect_stats['mean']:.4f} "
            f"median={defect_stats['median']:.4f} "
            f"max={defect_stats['max']:.4f}"
        )

    results_df = pd.DataFrame(results)
    scores_df = pd.DataFrame(score_records)

    scores_output_path = (
        PROJECT_ROOT
        / "ai"
        / "evaluation"
        / "confidence_scores.csv"
    )

    scores_df.to_csv(
        scores_output_path,
        index=False,
)

    output_path = (
        PROJECT_ROOT
        / "ai"
        / "evaluation"
        / "confidence_analysis_results.csv"
    )

    results_df.to_csv(
        output_path,
        index=False,
    )

    print("\nConfidence analysis results:")
    print(
        results_df.to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()