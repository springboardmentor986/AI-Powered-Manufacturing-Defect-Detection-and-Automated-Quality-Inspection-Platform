from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr, spearmanr
from torchvision import models


# ============================================================
# PROJECT PATHS
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
# DATASET FUNCTIONS
# ============================================================

def get_normal_images(category):
    """
    Return all train/good images.
    """

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
    """
    Return only defective test images.

    test/good is intentionally excluded.
    """

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
    """
    80% → normal feature memory
    20% → normal validation
    """

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


def get_ground_truth_mask(image_path):
    """
    Find MVTec ground-truth mask.
    """

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
    """
    Same preprocessing used by our detector.
    """

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
    """
    Layer3 output:

        [1, 256, 14, 14]

    converted to:

        [196, 256]
    """

    image = preprocess_image(
        image_path
    )

    feature_map = feature_extractor(
        image
    )

    local_features = (
        feature_map
        .permute(0, 2, 3, 1)
        .reshape(
            1,
            -1,
            feature_map.shape[1]
        )
    )

    return local_features[0]


# ============================================================
# NORMAL MEMORY
# ============================================================

def build_normal_memory(
    image_paths
):
    """
    Build category-specific normal
    patch feature memory.
    """

    features = []

    total = len(image_paths)

    for index, image_path in enumerate(
        image_paths,
        start=1
    ):

        image_features = extract_features(
            image_path
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
    """
    Nearest-normal-patch distance.
    """

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
# ACTUAL DEFECT AREA
# ============================================================

def calculate_actual_area(mask):
    """
    Actual defect percentage.

    ONLY used for evaluation.
    """

    return (
        np.count_nonzero(mask > 0)
        / mask.size
        * 100.0
    )


# ============================================================
# NORMALIZE ANOMALY MAP
# ============================================================

def normalize_anomaly_map(
    anomaly_map
):
    """
    Convert anomaly scores into
    relative anomaly weights.

    This removes the absolute scale
    of the anomaly distances.

    Result:
        values >= 0
        sum = 1
    """

    values = anomaly_map.astype(
        np.float64
    )

    values = values - values.min()

    total = values.sum()

    if total <= 0:

        return np.ones_like(
            values
        ) / values.size

    return values / total


# ============================================================
# SIZE MEASURES
# ============================================================

def calculate_size_measures(
    anomaly_map
):
    """
    Calculate several continuous
    measures of anomaly spread.

    None of these uses ground truth.
    """

    values = anomaly_map.astype(
        np.float64
    )

    flattened = values.flatten()

    # --------------------------------------------------------
    # 1. Mean anomaly
    # --------------------------------------------------------

    mean_anomaly = (
        np.mean(flattened)
    )

    # --------------------------------------------------------
    # 2. RMS anomaly
    #
    # Strong anomalies contribute more.
    # --------------------------------------------------------

    rms_anomaly = np.sqrt(
        np.mean(
            flattened ** 2
        )
    )

    # --------------------------------------------------------
    # 3. Top 10% mean anomaly
    # --------------------------------------------------------

    top_k = max(
        1,
        int(
            len(flattened)
            * 0.10
        )
    )

    top_values = np.sort(
        flattened
    )[-top_k:]

    top10_mean = (
        np.mean(top_values)
    )

    # --------------------------------------------------------
    # 4. Mean / maximum
    #
    # If anomaly is concentrated:
    #
    # mean / max → smaller
    #
    # If anomaly is spread:
    #
    # mean / max → larger
    # --------------------------------------------------------

    maximum = np.max(
        flattened
    )

    if maximum > 0:

        mean_max_ratio = (
            mean_anomaly
            / maximum
        )

    else:

        mean_max_ratio = 0.0

    # --------------------------------------------------------
    # 5. Effective anomalous area
    #
    # Normalize anomaly values into weights.
    #
    # Then calculate effective number of active patches.
    #
    # Formula:
    #
    # 1 / sum(p_i^2)
    #
    # This is small when anomaly is concentrated
    # and large when anomaly is spread out.
    # --------------------------------------------------------

    weights = normalize_anomaly_map(
        values
    )

    effective_patches = (
        1.0
        / np.sum(
            weights ** 2
        )
    )

    effective_area_percentage = (
        effective_patches
        / len(flattened)
        * 100.0
    )

    # --------------------------------------------------------
    # 6. Entropy
    #
    # Measures how spread out the anomaly
    # distribution is.
    # --------------------------------------------------------

    positive_weights = (
        weights[
            weights > 0
        ]
    )

    entropy = -np.sum(
        positive_weights
        * np.log(
            positive_weights
        )
    )

    maximum_entropy = np.log(
        len(flattened)
    )

    if maximum_entropy > 0:

        normalized_entropy = (
            entropy
            / maximum_entropy
        )

    else:

        normalized_entropy = 0.0

    return {
        "mean_anomaly":
            float(mean_anomaly),

        "rms_anomaly":
            float(rms_anomaly),

        "top10_mean_anomaly":
            float(top10_mean),

        "mean_max_ratio":
            float(mean_max_ratio),

        "effective_area_percentage":
            float(
                effective_area_percentage
            ),

        "normalized_entropy":
            float(
                normalized_entropy
            ),
    }


# ============================================================
# CORRELATION
# ============================================================

def calculate_correlation(
    actual,
    estimated
):
    """
    Return Pearson and Spearman.
    """

    actual = np.asarray(
        actual,
        dtype=np.float64
    )

    estimated = np.asarray(
        estimated,
        dtype=np.float64
    )

    if len(actual) < 2:

        return np.nan, np.nan

    pearson_value, _ = pearsonr(
        actual,
        estimated
    )

    spearman_value, _ = spearmanr(
        actual,
        estimated
    )

    return (
        float(pearson_value),
        float(spearman_value)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("Continuous Anomaly-Spread Size Analysis")

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
            "Building normal memory..."
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
        # DEFECTIVE IMAGES
        # ----------------------------------------------------

        defective_images = (
            get_defective_images(
                category
            )
        )

        rng = np.random.default_rng(
            RANDOM_SEED
        )

        defective_images = list(
            defective_images
        )

        rng.shuffle(
            defective_images
        )

        print(
            f"Defective images: "
            f"{len(defective_images)}"
        )

        # ----------------------------------------------------
        # PROCESS DEFECTIVE IMAGES
        # ----------------------------------------------------

        for index, image_path in enumerate(
            defective_images,
            start=1
        ):

            image_features = (
                extract_features(
                    image_path
                )
            )

            anomaly_map = (
                calculate_anomaly_map(
                    image_features,
                    normal_memory
                )
            )

            anomaly_map = (
                anomaly_map
                .detach()
                .cpu()
                .numpy()
            )

            ground_truth_mask = (
                get_ground_truth_mask(
                    image_path
                )
            )

            actual_area = (
                calculate_actual_area(
                    ground_truth_mask
                )
            )

            size_measures = (
                calculate_size_measures(
                    anomaly_map
                )
            )

            record = {
                "category":
                    category,

                "image_path":
                    str(image_path),

                "actual_defect_percentage":
                    actual_area,
            }

            record.update(
                size_measures
            )

            all_results.append(
                record
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

    measure_columns = [
        "mean_anomaly",
        "rms_anomaly",
        "top10_mean_anomaly",
        "mean_max_ratio",
        "effective_area_percentage",
        "normalized_entropy",
    ]

    # ========================================================
    # OVERALL CORRELATION
    # ========================================================

    print("\nOverall Correlation:")

    overall_rows = []

    actual = results_df[
        "actual_defect_percentage"
    ].to_numpy()

    for measure in measure_columns:

        estimated = results_df[
            measure
        ].to_numpy()

        pearson_value, spearman_value = (
            calculate_correlation(
                actual,
                estimated
            )
        )

        overall_rows.append(
            {
                "measure":
                    measure,

                "pearson":
                    pearson_value,

                "spearman":
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
    # CATEGORY CORRELATION
    # ========================================================

    print("\nCategory Correlation:")

    category_rows = []

    for category, group in (
        results_df.groupby(
            "category"
        )
    ):

        actual = group[
            "actual_defect_percentage"
        ].to_numpy()

        for measure in measure_columns:

            estimated = group[
                measure
            ].to_numpy()

            pearson_value, spearman_value = (
                calculate_correlation(
                    actual,
                    estimated
                )
            )

            category_rows.append(
                {
                    "category":
                        category,

                    "measure":
                        measure,

                    "pearson":
                        pearson_value,

                    "spearman":
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
    # SAVE RESULTS
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    detailed_path = (
        OUTPUT_DIR
        / "size_spread_results.csv"
    )

    overall_path = (
        OUTPUT_DIR
        / "size_spread_overall.csv"
    )

    category_path = (
        OUTPUT_DIR
        / "size_spread_category.csv"
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

    print(
        detailed_path
    )

    print(
        overall_path
    )

    print(
        category_path
    )


if __name__ == "__main__":
    main()