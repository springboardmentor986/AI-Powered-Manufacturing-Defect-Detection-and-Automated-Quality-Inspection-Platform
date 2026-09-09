from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from torchvision import models


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = (
    PROJECT_ROOT / "mvtec_anomaly_detection"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "ai" / "evaluation"
)


# ============================================================
# CONFIGURATION
# ============================================================

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

RANDOM_SEED = 42

NORMAL_VALIDATION_RATIO = 0.20

K_VALUES = [
    1.0,
    2.0,
    2.5,
    3.0,
    3.5,
    4.0,
]


# ============================================================
# DEVICE
# ============================================================

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

print(f"Using device: {DEVICE}")


# ============================================================
# RESNET18 LAYER3
# ============================================================

print("Loading pretrained ResNet18...")

base_model = models.resnet18(
    weights=models.ResNet18_Weights.DEFAULT
)

feature_extractor = torch.nn.Sequential(
    base_model.conv1,
    base_model.bn1,
    base_model.relu,
    base_model.maxpool,
    base_model.layer1,
    base_model.layer2,
    base_model.layer3,
).to(DEVICE)

feature_extractor.eval()

print("Feature extractor ready.")


# ============================================================
# DATASET
# ============================================================

def get_normal_images(category):

    directory = (
        DATASET_ROOT
        / category
        / "train"
        / "good"
    )

    return sorted(
        directory.glob("*.png")
    )


def get_defective_images(category):

    test_directory = (
        DATASET_ROOT
        / category
        / "test"
    )

    images = []

    for defect_directory in sorted(
        test_directory.iterdir()
    ):

        if not defect_directory.is_dir():
            continue

        if defect_directory.name == "good":
            continue

        images.extend(
            sorted(
                defect_directory.glob("*.png")
            )
        )

    return images


def split_normal_images(image_paths):

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    shuffled = list(image_paths)

    rng.shuffle(shuffled)

    split_index = int(
        len(shuffled)
        * (1 - NORMAL_VALIDATION_RATIO)
    )

    memory_images = (
        shuffled[:split_index]
    )

    validation_images = (
        shuffled[split_index:]
    )

    return (
        memory_images,
        validation_images,
    )


# ============================================================
# GROUND TRUTH
# ============================================================

def get_ground_truth_mask(image_path):

    image_path = Path(image_path)

    category_directory = (
        image_path
        .parent
        .parent
        .parent
    )

    defect_type = (
        image_path.parent.name
    )

    mask_path = (
        category_directory
        / "ground_truth"
        / defect_type
        / f"{image_path.stem}_mask.png"
    )

    if not mask_path.exists():

        raise FileNotFoundError(
            f"Ground-truth mask not found:\n"
            f"{mask_path}"
        )

    mask = cv2.imread(
        str(mask_path),
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:

        raise ValueError(
            f"Could not read mask:\n"
            f"{mask_path}"
        )

    return mask


# ============================================================
# PREPROCESSING
# ============================================================

def preprocess_image(image_path):

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise ValueError(
            f"Could not read image:\n"
            f"{image_path}"
        )

    rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    resized = cv2.resize(
        rgb,
        (224, 224)
    )

    image_float = (
        resized.astype(np.float32)
        / 255.0
    )

    tensor = torch.from_numpy(
        image_float
    )

    tensor = tensor.permute(
        2,
        0,
        1
    )

    tensor = tensor.unsqueeze(0)

    return tensor.to(DEVICE)


# ============================================================
# FEATURE EXTRACTION
# ============================================================

@torch.no_grad()
def extract_features(image_path):

    image = preprocess_image(
        image_path
    )

    feature_map = feature_extractor(
        image
    )

    # [1, 256, 14, 14]
    local_features = (
        feature_map
        .permute(0, 2, 3, 1)
        .reshape(
            1,
            -1,
            feature_map.shape[1]
        )
    )

    # [196, 256]
    return local_features[0]


# ============================================================
# NORMAL MEMORY
# ============================================================

def build_normal_memory(
    image_paths
):

    features = []

    total = len(image_paths)

    for index, image_path in enumerate(
        image_paths,
        start=1
    ):

        image_features = (
            extract_features(
                image_path
            )
        )

        features.append(
            image_features
        )

        if (
            index % 20 == 0
            or index == total
        ):

            print(
                f"    Memory images: "
                f"{index}/{total}"
            )

    return torch.cat(
        features,
        dim=0
    )


# ============================================================
# ANOMALY MAP
# ============================================================

@torch.no_grad()
def calculate_anomaly_map(
    image_features,
    normal_memory
):

    distances = torch.cdist(
        image_features,
        normal_memory
    )

    nearest_distances = (
        distances
        .min(dim=1)
        .values
    )

    return nearest_distances.reshape(
        14,
        14
    )


# ============================================================
# PIXEL METRICS
# ============================================================

def calculate_pixel_metrics(
    predicted_mask,
    ground_truth_mask
):

    predicted = (
        predicted_mask > 0
    )

    ground_truth = (
        ground_truth_mask > 0
    )

    true_positive = np.logical_and(
        predicted,
        ground_truth
    ).sum()

    false_positive = np.logical_and(
        predicted,
        np.logical_not(ground_truth)
    ).sum()

    false_negative = np.logical_and(
        np.logical_not(predicted),
        ground_truth
    ).sum()

    true_negative = np.logical_and(
        np.logical_not(predicted),
        np.logical_not(ground_truth)
    ).sum()

    precision_denominator = (
        true_positive
        + false_positive
    )

    recall_denominator = (
        true_positive
        + false_negative
    )

    if precision_denominator > 0:

        precision = (
            true_positive
            / precision_denominator
        )

    else:

        precision = 0.0

    if recall_denominator > 0:

        recall = (
            true_positive
            / recall_denominator
        )

    else:

        recall = 0.0

    if (
        precision + recall
        > 0
    ):

        f1 = (
            2
            * precision
            * recall
            / (
                precision
                + recall
            )
        )

    else:

        f1 = 0.0

    union = np.logical_or(
        predicted,
        ground_truth
    ).sum()

    intersection = true_positive

    if union > 0:

        iou = (
            intersection
            / union
        )

    else:

        iou = 0.0

    actual_area = (
        ground_truth.mean()
        * 100.0
    )

    predicted_area = (
        predicted.mean()
        * 100.0
    )

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "iou": float(iou),
        "actual_area": float(actual_area),
        "predicted_area": float(predicted_area),
        "true_negative": int(true_negative),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("Anomaly-Map Segmentation Threshold Analysis")

    all_results = []

    for category in CATEGORIES:
        print(f"\nCategory: {category}")

        # ----------------------------------------------------
        # NORMAL DATA
        # ----------------------------------------------------

        normal_images = (
            get_normal_images(
                category
            )
        )

        if not normal_images:

            print(
                "No normal images found."
            )

            continue

        (
            memory_images,
            normal_validation_images,
        ) = split_normal_images(
            normal_images
        )

        print(
            f"Normal images: "
            f"{len(normal_images)}"
        )

        print(
            f"Memory images: "
            f"{len(memory_images)}"
        )

        print(
            f"Normal validation images: "
            f"{len(normal_validation_images)}"
        )

        # ----------------------------------------------------
        # NORMAL MEMORY
        # ----------------------------------------------------

        print()
        print(
            "Building normal feature memory..."
        )

        normal_memory = (
            build_normal_memory(
                memory_images
            )
        )

        print(
            f"Memory shape: "
            f"{tuple(normal_memory.shape)}"
        )

        # ----------------------------------------------------
        # NORMAL VALIDATION ANOMALY MAPS
        # ----------------------------------------------------

        print()
        print(
            "Calculating normal validation "
            "anomaly maps..."
        )

        normal_values = []

        total_normal = (
            len(normal_validation_images)
        )

        for index, image_path in enumerate(
            normal_validation_images,
            start=1
        ):

            features = extract_features(
                image_path
            )

            anomaly_map = (
                calculate_anomaly_map(
                    features,
                    normal_memory
                )
            )

            values = (
                anomaly_map
                .detach()
                .cpu()
                .numpy()
                .flatten()
            )

            normal_values.extend(
                values
            )

            if (
                index % 20 == 0
                or index == total_normal
            ):

                print(
                    f"    Normal validation: "
                    f"{index}/{total_normal}"
                )

        normal_values = np.asarray(
            normal_values,
            dtype=np.float64
        )

        normal_mean = (
            normal_values.mean()
        )

        normal_std = (
            normal_values.std()
        )

        print()
        print(
            f"Normal patch mean: "
            f"{normal_mean:.6f}"
        )

        print(
            f"Normal patch std: "
            f"{normal_std:.6f}"
        )

        # ----------------------------------------------------
        # CALCULATE THRESHOLDS
        # ----------------------------------------------------

        thresholds = {}

        print()
        print(
            "Learned thresholds:"
        )

        for k in K_VALUES:

            threshold = (
                normal_mean
                + k * normal_std
            )

            thresholds[k] = threshold

            print(
                f"    k={k}: "
                f"{threshold:.6f}"
            )

        # ----------------------------------------------------
        # DEFECTIVE IMAGES
        # ----------------------------------------------------

        defective_images = (
            get_defective_images(
                category
            )
        )

        print()
        print(
            f"Defective images: "
            f"{len(defective_images)}"
        )

        # ----------------------------------------------------
        # EVALUATE
        # ----------------------------------------------------

        for index, image_path in enumerate(
            defective_images,
            start=1
        ):

            features = extract_features(
                image_path
            )

            anomaly_map = (
                calculate_anomaly_map(
                    features,
                    normal_memory
                )
            )

            anomaly_map = (
                anomaly_map
                .detach()
                .cpu()
                .numpy()
            )

            # --------------------------------------------
            # Resize anomaly map to image resolution
            # --------------------------------------------

            image = cv2.imread(
                str(image_path)
            )

            original_height, original_width = (
                image.shape[:2]
            )

            heatmap = cv2.resize(
                anomaly_map.astype(
                    np.float32
                ),
                (
                    original_width,
                    original_height
                ),
                interpolation=cv2.INTER_LINEAR
            )

            ground_truth_mask = (
                get_ground_truth_mask(
                    image_path
                )
            )

            # --------------------------------------------
            # Evaluate every k
            # --------------------------------------------

            for k, threshold in (
                thresholds.items()
            ):

                predicted_mask = (
                    heatmap >= threshold
                ).astype(
                    np.uint8
                )

                metrics = (
                    calculate_pixel_metrics(
                        predicted_mask,
                        ground_truth_mask
                    )
                )

                all_results.append(
                    {
                        "category":
                            category,

                        "image_path":
                            str(image_path),

                        "k":
                            k,

                        "threshold":
                            threshold,

                        "normal_mean":
                            normal_mean,

                        "normal_std":
                            normal_std,

                        "precision":
                            metrics[
                                "precision"
                            ],

                        "recall":
                            metrics[
                                "recall"
                            ],

                        "f1":
                            metrics[
                                "f1"
                            ],

                        "iou":
                            metrics[
                                "iou"
                            ],

                        "actual_area":
                            metrics[
                                "actual_area"
                            ],

                        "predicted_area":
                            metrics[
                                "predicted_area"
                            ],
                    }
                )

            if (
                index % 20 == 0
                or index == len(
                    defective_images
                )
            ):

                print(
                    f"    Defective images: "
                    f"{index}/"
                    f"{len(defective_images)}"
                )

    # ========================================================
    # RESULTS
    # ========================================================

    if not all_results:

        print(
            "\nNo results generated."
        )

        return

    results_df = pd.DataFrame(
        all_results
    )

    # ========================================================
    # OVERALL SUMMARY
    # ========================================================

    print("\nOverall Summary:")

    overall_rows = []

    for k, group in (
        results_df.groupby("k")
    ):

        actual = group[
            "actual_area"
        ].to_numpy()

        predicted = group[
            "predicted_area"
        ].to_numpy()

        # --------------------------------------------
        # Correlation between predicted and actual area
        # --------------------------------------------

        if len(actual) >= 2:

            from scipy.stats import (
                pearsonr,
                spearmanr,
            )

            pearson_value, _ = pearsonr(
                actual,
                predicted
            )

            spearman_value, _ = spearmanr(
                actual,
                predicted
            )

        else:

            pearson_value = np.nan
            spearman_value = np.nan

        overall_rows.append(
            {
                "k":
                    k,

                "threshold":
                    group[
                        "threshold"
                    ].iloc[0],

                "precision":
                    group[
                        "precision"
                    ].mean(),

                "recall":
                    group[
                        "recall"
                    ].mean(),

                "f1":
                    group[
                        "f1"
                    ].mean(),

                "iou":
                    group[
                        "iou"
                    ].mean(),

                "mean_actual_area":
                    actual.mean(),

                "mean_predicted_area":
                    predicted.mean(),

                "pearson_area":
                    pearson_value,

                "spearman_area":
                    spearman_value,
            }
        )

    overall_df = pd.DataFrame(
        overall_rows
    )

    print(
        overall_df.to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}"
        )
    )

    # ========================================================
    # CATEGORY SUMMARY
    # ========================================================

    print("\nCategory Summary:")

    category_rows = []

    from scipy.stats import (
        pearsonr,
        spearmanr,
    )

    for (
        category,
        k,
    ), group in results_df.groupby(
        [
            "category",
            "k",
        ]
    ):

        actual = group[
            "actual_area"
        ].to_numpy()

        predicted = group[
            "predicted_area"
        ].to_numpy()

        if len(actual) >= 2:

            pearson_value, _ = pearsonr(
                actual,
                predicted
            )

            spearman_value, _ = spearmanr(
                actual,
                predicted
            )

        else:

            pearson_value = np.nan
            spearman_value = np.nan

        category_rows.append(
            {
                "category":
                    category,

                "k":
                    k,

                "precision":
                    group[
                        "precision"
                    ].mean(),

                "recall":
                    group[
                        "recall"
                    ].mean(),

                "f1":
                    group[
                        "f1"
                    ].mean(),

                "iou":
                    group[
                        "iou"
                    ].mean(),

                "mean_actual_area":
                    actual.mean(),

                "mean_predicted_area":
                    predicted.mean(),

                "pearson_area":
                    pearson_value,

                "spearman_area":
                    spearman_value,
            }
        )

    category_df = pd.DataFrame(
        category_rows
    )

    print(
        category_df.to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}"
        )
    )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    detailed_path = (
        OUTPUT_DIR
        / "segmentation_threshold_results.csv"
    )

    overall_path = (
        OUTPUT_DIR
        / "segmentation_threshold_overall.csv"
    )

    category_path = (
        OUTPUT_DIR
        / "segmentation_threshold_category.csv"
    )

    results_df.to_csv(
        detailed_path,
        index=False
    )

    overall_df.to_csv(
        overall_path,
        index=False
    )

    category_df.to_csv(
        category_path,
        index=False
    )

    print("\nFiles Saved:")

    print(detailed_path)
    print(overall_path)
    print(category_path)


if __name__ == "__main__":
    main()