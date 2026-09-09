from pathlib import Path
import csv

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader

from ai.evaluation.segmentation_dataset import (
    MVTecSegmentationDataset,
)
from ai.models.defect_segmenter import UNet


# ============================================================
# Configuration
# ============================================================

MODEL_PATH = Path(
    "ai/models/defect_segmenter_unet.pt"
)

THRESHOLD_PATH = Path(
    "ai/models/segmentation_threshold.txt"
)

SPLIT_DIRECTORY = Path(
    "ai/evaluation/segmentation_splits"
)

BATCH_SIZE = 8


# ============================================================
# Device
# ============================================================

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

print(f"Using device: {DEVICE}")


# ============================================================
# Load test samples
# ============================================================

def load_test_samples():

    samples = []

    test_csv = SPLIT_DIRECTORY / "test.csv"

    with open(
        test_csv,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            samples.append(
                (
                    row["image_path"],
                    row["mask_path"],
                )
            )

    return samples


# ============================================================
# Get category from image path
# ============================================================

def get_category(image_path):

    """
    MVTec path structure:

    category/
        test/
            defect_type/
                image.png

    Therefore:

    image_path.parent          -> defect_type
    image_path.parent.parent  -> test
    image_path.parent.parent.parent -> category
    """

    path = Path(image_path)

    return path.parent.parent.parent.name


# ============================================================
# Metric: Pixel Precision / Recall / F1 / IoU
# ============================================================

def calculate_pixel_metrics(
    predictions,
    targets,
):

    predictions = predictions.astype(bool)
    targets = targets.astype(bool)

    true_positive = np.logical_and(
        predictions,
        targets,
    ).sum()

    false_positive = np.logical_and(
        predictions,
        ~targets,
    ).sum()

    false_negative = np.logical_and(
        ~predictions,
        targets,
    ).sum()

    # Precision
    precision_denominator = (
        true_positive + false_positive
    )

    if precision_denominator == 0:
        precision = 0.0
    else:
        precision = (
            true_positive
            / precision_denominator
        )

    # Recall
    recall_denominator = (
        true_positive + false_negative
    )

    if recall_denominator == 0:
        recall = 0.0
    else:
        recall = (
            true_positive
            / recall_denominator
        )

    # F1
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
        )

    # IoU
    union = np.logical_or(
        predictions,
        targets,
    ).sum()

    if union == 0:
        iou = 1.0
    else:
        iou = (
            true_positive
            / union
        )

    return (
        float(precision),
        float(recall),
        float(f1),
        float(iou),
    )


# ============================================================
# Pearson correlation
# ============================================================

def calculate_pearson(
    actual,
    predicted,
):

    actual = np.asarray(
        actual,
        dtype=np.float64,
    )

    predicted = np.asarray(
        predicted,
        dtype=np.float64,
    )

    if len(actual) < 2:
        return 0.0

    if (
        np.std(actual) == 0
        or np.std(predicted) == 0
    ):
        return 0.0

    correlation = np.corrcoef(
        actual,
        predicted,
    )[0, 1]

    if np.isnan(correlation):
        return 0.0

    return float(correlation)


# ============================================================
# Spearman correlation
# ============================================================

def calculate_spearman(
    actual,
    predicted,
):

    actual = np.asarray(
        actual,
        dtype=np.float64,
    )

    predicted = np.asarray(
        predicted,
        dtype=np.float64,
    )

    if len(actual) < 2:
        return 0.0

    # Convert values to ranks
    actual_order = np.argsort(actual)
    predicted_order = np.argsort(predicted)

    actual_ranks = np.empty(
        len(actual),
        dtype=np.float64,
    )

    predicted_ranks = np.empty(
        len(predicted),
        dtype=np.float64,
    )

    actual_ranks[actual_order] = np.arange(
        len(actual)
    )

    predicted_ranks[predicted_order] = np.arange(
        len(predicted)
    )

    if (
        np.std(actual_ranks) == 0
        or np.std(predicted_ranks) == 0
    ):
        return 0.0

    correlation = np.corrcoef(
        actual_ranks,
        predicted_ranks,
    )[0, 1]

    if np.isnan(correlation):
        return 0.0

    return float(correlation)


# ============================================================
# Load threshold
# ============================================================

with open(
    THRESHOLD_PATH,
    "r",
) as file:

    threshold = float(
        file.read().strip()
    )

print(
    f"Frozen threshold: {threshold:.4f}"
)


# ============================================================
# Load test dataset
# ============================================================

test_samples = load_test_samples()

test_dataset = MVTecSegmentationDataset(
    test_samples,
    image_size=224,
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
)

print(
    f"Test samples: {len(test_dataset)}"
)


# ============================================================
# Load model
# ============================================================

model = UNet(
    in_channels=3,
    out_channels=1,
)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=True,
)

model.load_state_dict(checkpoint)

model = model.to(DEVICE)

model.eval()

print(
    f"Loaded model: {MODEL_PATH}"
)


# ============================================================
# Storage
# ============================================================

overall_predictions = []
overall_targets = []

overall_actual_areas = []
overall_predicted_areas = []


# Category-wise storage

category_data = {}


for image_path, mask_path in test_samples:

    category = get_category(
        image_path
    )

    if category not in category_data:

        category_data[category] = {
            "predictions": [],
            "targets": [],
            "actual_areas": [],
            "predicted_areas": [],
        }


# ============================================================
# Evaluation
# ============================================================

print()
print("Evaluating test images...")
print()


sample_index = 0


with torch.no_grad():

    for images, masks in test_loader:

        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        # ----------------------------------------------------
        # Model prediction
        # ----------------------------------------------------

        logits = model(images)

        probabilities = torch.sigmoid(
            logits
        )

        predictions = (
            probabilities >= threshold
        ).float()

        # ----------------------------------------------------
        # Move to CPU
        # ----------------------------------------------------

        predictions_np = (
            predictions
            .cpu()
            .numpy()
        )

        masks_np = (
            masks
            .cpu()
            .numpy()
        )

        # ----------------------------------------------------
        # Process every image
        # ----------------------------------------------------

        for prediction, target in zip(
            predictions_np,
            masks_np,
        ):

            prediction = prediction[0].astype(np.uint8)
            target = target[0]

            # Apply validated post-processing (morphological opening + connected components)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            opened = cv2.morphologyEx(prediction, cv2.MORPH_OPEN, kernel)
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(opened)
            cleaned = np.zeros_like(opened)
            for lbl in range(1, num_labels):
                if stats[lbl, cv2.CC_STAT_AREA] >= 25:
                    cleaned[labels == lbl] = 1
            prediction = cleaned

            # -----------------------------------------------
            # Overall storage
            # -----------------------------------------------

            overall_predictions.append(
                prediction
            )

            overall_targets.append(
                target
            )

            # -----------------------------------------------
            # Area percentages
            # -----------------------------------------------

            actual_area = (
                np.sum(target > 0)
                / target.size
                * 100
            )

            predicted_area = (
                np.sum(prediction > 0)
                / prediction.size
                * 100
            )

            overall_actual_areas.append(
                actual_area
            )

            overall_predicted_areas.append(
                predicted_area
            )

            # -----------------------------------------------
            # Category
            # -----------------------------------------------

            image_path = test_samples[
                sample_index
            ][0]

            category = get_category(
                image_path
            )

            category_data[
                category
            ]["predictions"].append(
                prediction
            )

            category_data[
                category
            ]["targets"].append(
                target
            )

            category_data[
                category
            ]["actual_areas"].append(
                actual_area
            )

            category_data[
                category
            ]["predicted_areas"].append(
                predicted_area
            )

            sample_index += 1


# ============================================================
# Overall metrics
# ============================================================

overall_predictions = np.asarray(
    overall_predictions
)

overall_targets = np.asarray(
    overall_targets
)


(
    overall_precision,
    overall_recall,
    overall_f1,
    overall_iou,
) = calculate_pixel_metrics(
    overall_predictions,
    overall_targets,
)


overall_actual_areas = np.asarray(
    overall_actual_areas,
    dtype=np.float64,
)

overall_predicted_areas = np.asarray(
    overall_predicted_areas,
    dtype=np.float64,
)


overall_pearson = calculate_pearson(
    overall_actual_areas,
    overall_predicted_areas,
)

overall_spearman = calculate_spearman(
    overall_actual_areas,
    overall_predicted_areas,
)


overall_area_errors = np.abs(
    overall_predicted_areas
    - overall_actual_areas
)

overall_mean_area_error = np.mean(
    overall_area_errors
)

overall_median_area_error = np.median(
    overall_area_errors
)


# ============================================================
# Print overall results
# ============================================================

print("\nOverall Test Results:")

print(
    f"Pixel Precision : {overall_precision:.4f}"
)

print(
    f"Pixel Recall    : {overall_recall:.4f}"
)

print(
    f"Pixel F1        : {overall_f1:.4f}"
)

print(
    f"Pixel IoU       : {overall_iou:.4f}"
)

print(
    f"Area Pearson    : {overall_pearson:.4f}"
)

print(
    f"Area Spearman   : {overall_spearman:.4f}"
)

print(
    f"Mean Area Error : {overall_mean_area_error:.4f}%"
)

print(
    f"Median Area Error: {overall_median_area_error:.4f}%"
)


# ============================================================
# Per-category evaluation
# ============================================================

category_metrics = []


for category in sorted(category_data.keys()):

    predictions = np.asarray(
        category_data[category][
            "predictions"
        ]
    )

    targets = np.asarray(
        category_data[category][
            "targets"
        ]
    )

    actual_areas = np.asarray(
        category_data[category][
            "actual_areas"
        ],
        dtype=np.float64,
    )

    predicted_areas = np.asarray(
        category_data[category][
            "predicted_areas"
        ],
        dtype=np.float64,
    )

    # --------------------------------------------------------
    # Pixel metrics
    # --------------------------------------------------------

    (
        precision,
        recall,
        f1,
        iou,
    ) = calculate_pixel_metrics(
        predictions,
        targets,
    )

    # --------------------------------------------------------
    # Area metrics
    # --------------------------------------------------------

    pearson = calculate_pearson(
        actual_areas,
        predicted_areas,
    )

    spearman = calculate_spearman(
        actual_areas,
        predicted_areas,
    )

    area_errors = np.abs(
        predicted_areas
        - actual_areas
    )

    mae = np.mean(
        area_errors
    )

    # --------------------------------------------------------
    # Save category result
    # --------------------------------------------------------

    category_metrics.append(
        {
            "category": category,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "iou": iou,
            "pearson": pearson,
            "spearman": spearman,
            "mae": mae,
        }
    )


# ============================================================
# Macro averages
# ============================================================

macro_precision = np.mean(
    [
        result["precision"]
        for result in category_metrics
    ]
)

macro_recall = np.mean(
    [
        result["recall"]
        for result in category_metrics
    ]
)

macro_f1 = np.mean(
    [
        result["f1"]
        for result in category_metrics
    ]
)

macro_iou = np.mean(
    [
        result["iou"]
        for result in category_metrics
    ]
)

macro_pearson = np.mean(
    [
        result["pearson"]
        for result in category_metrics
    ]
)

macro_spearman = np.mean(
    [
        result["spearman"]
        for result in category_metrics
    ]
)

macro_mae = np.mean(
    [
        result["mae"]
        for result in category_metrics
    ]
)


# ============================================================
# Print per-category results
# ============================================================

print("\nPer-Category Results:")

print(
    f"{'Category':<15}"
    f"{'Precision':>12}"
    f"{'Recall':>12}"
    f"{'F1':>12}"
    f"{'IoU':>12}"
    f"{'Pearson':>12}"
    f"{'Spearman':>12}"
    f"{'MAE %':>12}"
)

for result in category_metrics:

    print(
        f"{result['category']:<15}"
        f"{result['precision']:>12.4f}"
        f"{result['recall']:>12.4f}"
        f"{result['f1']:>12.4f}"
        f"{result['iou']:>12.4f}"
        f"{result['pearson']:>12.4f}"
        f"{result['spearman']:>12.4f}"
        f"{result['mae']:>12.4f}"
    )

print(
    f"{'MACRO AVG':<15}"
    f"{macro_precision:>12.4f}"
    f"{macro_recall:>12.4f}"
    f"{macro_f1:>12.4f}"
    f"{macro_iou:>12.4f}"
    f"{macro_pearson:>12.4f}"
    f"{macro_spearman:>12.4f}"
    f"{macro_mae:>12.4f}"
)

print("Final per-category evaluation complete.")