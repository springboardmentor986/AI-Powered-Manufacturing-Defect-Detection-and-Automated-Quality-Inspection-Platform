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

DATASET_ROOT = PROJECT_ROOT / "mvtec_anomaly_detection"

OUTPUT_DIR = PROJECT_ROOT / "ai" / "evaluation"


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

# Thresholds learned from NORMAL validation patches.
THRESHOLD_PERCENTILES = [
    95,
    97.5,
    99,
    99.5,
]

RANDOM_SEED = 42

NORMAL_VALIDATION_RATIO = 0.20

# None = use every defective image.
MAX_DEFECTIVE_IMAGES = None


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
# RESNET18 LAYER3 FEATURE EXTRACTOR
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
# DATASET HELPERS
# ============================================================

def get_normal_images(category):
    """
    Get all train/good images for a category.
    """

    directory = (
        DATASET_ROOT
        / category
        / "train"
        / "good"
    )

    return sorted(directory.glob("*.png"))


def get_defective_images(category):
    """
    Get only defective test images.

    MVTec structure:

        test/
            good/
            defect_type_1/
            defect_type_2/
            ...

    We explicitly exclude "good".
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

        # IMPORTANT:
        # test/good contains normal images and
        # has no ground-truth defect masks.
        if defect_directory.name == "good":
            continue

        for image_path in sorted(
            defect_directory.glob("*.png")
        ):

            images.append(image_path)

    return images


def split_normal_images(image_paths):
    """
    Split train/good images into:

    80% → normal feature memory
    20% → normal validation
    """

    image_paths = list(image_paths)

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    shuffled = image_paths.copy()

    rng.shuffle(shuffled)

    split_index = int(
        len(shuffled)
        * (1 - NORMAL_VALIDATION_RATIO)
    )

    memory_images = shuffled[:split_index]

    validation_images = shuffled[split_index:]

    return memory_images, validation_images


def get_ground_truth_mask(image_path):
    """
    Find the official MVTec ground-truth mask.

    Expected image structure:

        category/
            test/
                defect_type/
                    image.png

    Expected mask structure:

        category/
            ground_truth/
                defect_type/
                    image_mask.png
    """

    image_path = Path(image_path)

    # Example:
    # .../bottle/test/crack/012.png
    #
    # image_path.parent.name
    # -> crack
    #
    # image_path.parent.parent.name
    # -> test
    #
    # image_path.parent.parent.parent.name
    # -> bottle

    defect_type = image_path.parent.name

    category_directory = (
        image_path.parent.parent.parent
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
            f"{mask_path}\n\n"
            f"Image:\n"
            f"{image_path}\n\n"
            f"Defect type:\n"
            f"{defect_type}"
        )

    mask = cv2.imread(
        str(mask_path),
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:

        raise ValueError(
            f"Could not read ground-truth mask:\n"
            f"{mask_path}"
        )

    return mask


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image_path):
    """
    Same preprocessing used by our Layer3 detector:

    BGR → RGB
    resize → 224 x 224
    /255
    HWC → CHW
    batch dimension
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

    tensor = tensor.to(DEVICE)

    return tensor


# ============================================================
# FEATURE EXTRACTION
# ============================================================

@torch.no_grad()
def extract_features(image_path):
    """
    Extract Layer3 local features.

    Output:

    [1, 256, 14, 14]

    then:

    [196, 256]
    """

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
# BUILD CATEGORY NORMAL MEMORY
# ============================================================

def build_normal_memory(
    image_paths
):
    """
    Build normal feature memory
    from the 80% normal training split.

    Each image produces:

    14 x 14 = 196 patches

    Each patch has 256 features.
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

        if index % 20 == 0 or index == total:

            print(
                f"    Memory images: "
                f"{index}/{total}"
            )

    memory = torch.cat(
        features,
        dim=0
    )

    return memory


# ============================================================
# CALCULATE ANOMALY MAP
# ============================================================

@torch.no_grad()
def calculate_anomaly_map(
    image_features,
    normal_memory
):
    """
    Compare every test patch against
    the nearest normal patch.

    image_features:
        [196, 256]

    normal_memory:
        [N, 256]

    output:
        [14, 14]
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

    anomaly_map = (
        nearest_distances
        .reshape(14, 14)
    )

    return anomaly_map


# ============================================================
# ACTUAL DEFECT AREA
# ============================================================

def calculate_actual_defect_percentage(
    mask
):
    """
    Calculate actual defect area.

    ONLY used for evaluation.
    """

    defect_pixels = np.count_nonzero(
        mask > 0
    )

    total_pixels = mask.size

    return (
        defect_pixels
        / total_pixels
        * 100.0
    )


# ============================================================
# ESTIMATED ANOMALOUS AREA
# ============================================================

def calculate_estimated_area(
    anomaly_map,
    threshold
):
    """
    Count how many anomaly-map patches
    exceed the learned normal threshold.

    This is our estimated anomalous area.
    """

    anomalous_patches = (
        anomaly_map >= threshold
    )

    estimated_percentage = (
        anomalous_patches
        .float()
        .mean()
        .item()
        * 100.0
    )

    return estimated_percentage


# ============================================================
# CORRELATION
# ============================================================

def calculate_correlations(
    actual,
    estimated
):
    """
    Calculate:

    Pearson:
        linear relationship

    Spearman:
        ranking relationship
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

    print("Size Estimation Experiment")

    all_results = []

    for category in CATEGORIES:
        print(f"\nCategory: {category}")

        # ----------------------------------------------------
        # NORMAL IMAGES
        # ----------------------------------------------------

        normal_images = get_normal_images(
            category
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
        # BUILD CATEGORY MEMORY
        # ----------------------------------------------------

        print()
        print(
            "Building category-specific "
            "normal feature memory..."
        )

        normal_memory = build_normal_memory(
            memory_images
        )

        print(
            f"Normal memory shape: "
            f"{tuple(normal_memory.shape)}"
        )

        # ----------------------------------------------------
        # NORMAL VALIDATION PATCH SCORES
        # ----------------------------------------------------

        print()
        print(
            "Calculating normal validation "
            "patch scores..."
        )

        normal_patch_scores = []

        total_normal = len(
            normal_validation_images
        )

        for index, image_path in enumerate(
            normal_validation_images,
            start=1
        ):

            image_features = extract_features(
                image_path
            )

            anomaly_map = calculate_anomaly_map(
                image_features,
                normal_memory
            )

            patch_scores = (
                anomaly_map
                .flatten()
                .detach()
                .cpu()
                .numpy()
            )

            normal_patch_scores.extend(
                patch_scores
            )

            if (
                index % 20 == 0
                or index == total_normal
            ):

                print(
                    f"    Validation images: "
                    f"{index}/{total_normal}"
                )

        normal_patch_scores = np.asarray(
            normal_patch_scores
        )

        # ----------------------------------------------------
        # LEARN THRESHOLDS
        # ----------------------------------------------------

        thresholds = {}

        print()
        print(
            "Normal patch thresholds:"
        )

        for percentile in (
            THRESHOLD_PERCENTILES
        ):

            threshold = np.percentile(
                normal_patch_scores,
                percentile
            )

            thresholds[
                percentile
            ] = threshold

            print(
                f"    {percentile}%: "
                f"{threshold:.6f}"
            )

        # ----------------------------------------------------
        # DEFECTIVE IMAGES
        # ----------------------------------------------------

        defective_images = get_defective_images(
            category
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

        if MAX_DEFECTIVE_IMAGES is not None:

            defective_images = (
                defective_images[
                    :MAX_DEFECTIVE_IMAGES
                ]
            )

        print()
        print(
            f"Defective validation images: "
            f"{len(defective_images)}"
        )

        # ----------------------------------------------------
        # EVALUATE DEFECTIVE IMAGES
        # ----------------------------------------------------

        for index, image_path in enumerate(
            defective_images,
            start=1
        ):

            image_features = extract_features(
                image_path
            )

            anomaly_map = calculate_anomaly_map(
                image_features,
                normal_memory
            )

            anomaly_map_cpu = (
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

            actual_percentage = (
                calculate_actual_defect_percentage(
                    ground_truth_mask
                )
            )

            # --------------------------------------------
            # Test every threshold
            # --------------------------------------------

            for (
                percentile,
                threshold
            ) in thresholds.items():

                estimated_percentage = (
                    calculate_estimated_area(
                        anomaly_map,
                        threshold
                    )
                )

                all_results.append(
                    {
                        "category": category,
                        "image_path": str(
                            image_path
                        ),
                        "threshold_percentile":
                            percentile,
                        "threshold":
                            threshold,
                        "actual_defect_percentage":
                            actual_percentage,
                        "estimated_anomalous_percentage":
                            estimated_percentage,
                    }
                )

            if (
                index % 20 == 0
                or index == len(defective_images)
            ):

                print(
                    f"    Defective images: "
                    f"{index}/"
                    f"{len(defective_images)}"
                )

    # ========================================================
    # CHECK RESULTS
    # ========================================================

    if not all_results:

        print()
        print(
            "No results generated."
        )

        return

    results_df = pd.DataFrame(
        all_results
    )

    # ========================================================
    # OVERALL SUMMARY
    # ========================================================

    print("\nOverall Size Estimation Summary:")

    summary_rows = []

    for percentile in (
        THRESHOLD_PERCENTILES
    ):

        threshold_df = results_df[
            results_df[
                "threshold_percentile"
            ]
            == percentile
        ]

        actual = threshold_df[
            "actual_defect_percentage"
        ].to_numpy()

        estimated = threshold_df[
            "estimated_anomalous_percentage"
        ].to_numpy()

        pearson_value, spearman_value = (
            calculate_correlations(
                actual,
                estimated
            )
        )

        summary_rows.append(
            {
                "threshold_percentile":
                    percentile,
                "mean_actual_defect_percentage":
                    actual.mean(),
                "mean_estimated_anomalous_percentage":
                    estimated.mean(),
                "pearson_correlation":
                    pearson_value,
                "spearman_correlation":
                    spearman_value,
            }
        )

    summary_df = pd.DataFrame(
        summary_rows
    )

    print(
        summary_df.to_string(
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

    for (
        category,
        percentile,
    ), group in results_df.groupby(
        [
            "category",
            "threshold_percentile",
        ]
    ):

        actual = group[
            "actual_defect_percentage"
        ].to_numpy()

        estimated = group[
            "estimated_anomalous_percentage"
        ].to_numpy()

        pearson_value, spearman_value = (
            calculate_correlations(
                actual,
                estimated
            )
        )

        category_rows.append(
            {
                "category":
                    category,
                "threshold_percentile":
                    percentile,
                "mean_actual_defect_percentage":
                    actual.mean(),
                "mean_estimated_anomalous_percentage":
                    estimated.mean(),
                "pearson_correlation":
                    pearson_value,
                "spearman_correlation":
                    spearman_value,
            }
        )

    category_summary_df = pd.DataFrame(
        category_rows
    )

    print(
        category_summary_df.to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}"
        )
    )

    # ========================================================
    # SAVE FILES
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    detailed_path = (
        OUTPUT_DIR
        / "size_estimation_results.csv"
    )

    summary_path = (
        OUTPUT_DIR
        / "size_estimation_summary.csv"
    )

    category_summary_path = (
        OUTPUT_DIR
        / "size_estimation_category_summary.csv"
    )

    results_df.to_csv(
        detailed_path,
        index=False
    )

    summary_df.to_csv(
        summary_path,
        index=False
    )

    category_summary_df.to_csv(
        category_summary_path,
        index=False
    )

    print()
    print(
        "Saved detailed results:"
    )

    print(
        detailed_path
    )

    print()
    print(
        "Saved overall summary:"
    )

    print(
        summary_path
    )

    print()
    print(
        "Saved category summary:"
    )

    print(
        category_summary_path
    )


if __name__ == "__main__":
    main()