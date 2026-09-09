from pathlib import Path
import csv

import numpy as np
import torch
from torch.utils.data import DataLoader

from ai.evaluation.segmentation_dataset import (
    MVTecSegmentationDataset,
)
from ai.models.defect_segmenter import UNet
from ai.models.size_scorer import SizeScorer


# ============================================================
# Configuration
# ============================================================

MODEL_PATH = Path(
    "ai/models/defect_segmenter_unet.pt"
)

THRESHOLD_PATH = Path(
    "ai/models/segmentation_threshold.txt"
)

BOUNDARIES_PATH = Path(
    "ai/models/size_score_boundaries.csv"
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
# Load CSV samples
# ============================================================

def load_samples(csv_path):

    samples = []

    with open(
        csv_path,
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
# Get category
# ============================================================

def get_category(image_path):

    path = Path(image_path)

    return path.parent.parent.parent.name


# ============================================================
# Load Size Score boundaries
# ============================================================

def load_boundaries():
    boundaries = {}

    with open(
        BOUNDARIES_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            category = row["category"]

            boundaries[category] = {
                "p10": float(row["p10"]),
                "p25": float(row["p25"]),
                "p50": float(row["p50"]),
                "p75": float(row["p75"]),
                "p90": float(row["p90"]),
                "p95": float(row["p95"]),
            }

    return boundaries

# ============================================================
# Load segmentation threshold
# ============================================================

with open(
    THRESHOLD_PATH,
    "r",
) as file:

    threshold = float(
        file.read().strip()
    )

print(
    f"Frozen segmentation threshold: {threshold:.4f}"
)


# ============================================================
# Load boundaries
# ============================================================

boundaries = load_boundaries()

print(
    f"Loaded size boundaries: {len(boundaries)} categories"
)


# ============================================================
# Create SizeScorer
# ============================================================

size_scorer = SizeScorer(
    boundaries
)


# ============================================================
# Load validation samples
# ============================================================

validation_samples = load_samples(
    SPLIT_DIRECTORY / "validation.csv"
)

print(
    f"Validation samples: {len(validation_samples)}"
)


# ============================================================
# Dataset / DataLoader
# ============================================================

validation_dataset = MVTecSegmentationDataset(
    validation_samples,
    image_size=224,
)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
)


# ============================================================
# Load U-Net
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

model.load_state_dict(
    checkpoint
)

model = model.to(DEVICE)

model.eval()

print(
    f"Loaded model: {MODEL_PATH}"
)


# ============================================================
# Storage
# ============================================================

records = []


# ============================================================
# Validation inference
# ============================================================

print()
print("Evaluating validation images...")
print()


sample_index = 0


with torch.no_grad():

    for images, masks in validation_loader:

        images = images.to(DEVICE)

        masks = masks.to(DEVICE)

        # ----------------------------------------------------
        # U-Net prediction
        # ----------------------------------------------------

        logits = model(images)

        probabilities = torch.sigmoid(
            logits
        )

        predictions = (
            probabilities >= threshold
        ).float()

        # ----------------------------------------------------
        # CPU
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
        # Process each image
        # ----------------------------------------------------

        for prediction, target in zip(
            predictions_np,
            masks_np,
        ):

            prediction = prediction[0]

            target = target[0]

            # -----------------------------------------------
            # Areas
            # -----------------------------------------------

            actual_area = (
                np.sum(target > 0)
                / target.size
                * 100.0
            )

            predicted_area = (
                np.sum(prediction > 0)
                / prediction.size
                * 100.0
            )

            # -----------------------------------------------
            # Category
            # -----------------------------------------------

            image_path = validation_samples[
                sample_index
            ][0]

            category = get_category(
                image_path
            )

            # -----------------------------------------------
            # Size Score
            # -----------------------------------------------

            size_score = size_scorer.calculate(
                category=category,
                predicted_area_percent=predicted_area,
            )

            records.append(
                {
                    "category": category,
                    "actual_area": actual_area,
                    "predicted_area": predicted_area,
                    "size_score": size_score,
                }
            )

            sample_index += 1


# ============================================================
# Overall correlation
# ============================================================

actual_areas = np.asarray(
    [
        record["actual_area"]
        for record in records
    ],
    dtype=np.float64,
)

size_scores = np.asarray(
    [
        record["size_score"]
        for record in records
    ],
    dtype=np.float64,
)


def pearson(x, y):

    if (
        len(x) < 2
        or np.std(x) == 0
        or np.std(y) == 0
    ):
        return 0.0

    value = np.corrcoef(
        x,
        y,
    )[0, 1]

    if np.isnan(value):
        return 0.0

    return float(value)


def spearman(x, y):

    if len(x) < 2:
        return 0.0

    x_order = np.argsort(x)
    y_order = np.argsort(y)

    x_rank = np.empty(
        len(x),
        dtype=np.float64,
    )

    y_rank = np.empty(
        len(y),
        dtype=np.float64,
    )

    x_rank[x_order] = np.arange(
        len(x),
        dtype=np.float64,
    )

    y_rank[y_order] = np.arange(
        len(y),
        dtype=np.float64,
    )

    return pearson(
        x_rank,
        y_rank,
    )


overall_pearson = pearson(
    actual_areas,
    size_scores,
)

overall_spearman = spearman(
    actual_areas,
    size_scores,
)


# ============================================================
# Per-category validation
# ============================================================

category_results = []


categories = sorted(
    set(
        record["category"]
        for record in records
    )
)


for category in categories:

    category_records = [
        record
        for record in records
        if record["category"] == category
    ]

    category_actual = np.asarray(
        [
            record["actual_area"]
            for record in category_records
        ],
        dtype=np.float64,
    )

    category_scores = np.asarray(
        [
            record["size_score"]
            for record in category_records
        ],
        dtype=np.float64,
    )

    category_pearson = pearson(
        category_actual,
        category_scores,
    )

    category_spearman = spearman(
        category_actual,
        category_scores,
    )

    category_results.append(
        {
            "category": category,
            "samples": len(category_records),
            "pearson": category_pearson,
            "spearman": category_spearman,
            "min_score": np.min(category_scores),
            "max_score": np.max(category_scores),
            "mean_score": np.mean(category_scores),
        }
    )


# ============================================================
# Print validation results
# ============================================================

print("\nSize Score Validation:")

print(
    f"Validation samples : {len(records)}"
)

print(
    f"Overall Pearson    : {overall_pearson:.4f}"
)

print(
    f"Overall Spearman   : {overall_spearman:.4f}"
)

print()

print(
    f"{'Category':<15}"
    f"{'Samples':>10}"
    f"{'Pearson':>12}"
    f"{'Spearman':>12}"
    f"{'Min Score':>12}"
    f"{'Max Score':>12}"
    f"{'Mean Score':>12}"
)

for result in category_results:

    print(
        f"{result['category']:<15}"
        f"{result['samples']:>10}"
        f"{result['pearson']:>12.4f}"
        f"{result['spearman']:>12.4f}"
        f"{result['min_score']:>12.2f}"
        f"{result['max_score']:>12.2f}"
        f"{result['mean_score']:>12.2f}"
    )

print("\nSize Scorer Edge Case Test:")

for category in sorted(boundaries.keys()):

    values = boundaries[category]

    p25 = values["p25"]
    p90 = values["p90"]

    low_score = size_scorer.calculate(
        category,
        0.0,
    )

    high_score = size_scorer.calculate(
        category,
        p90 + 100.0,
    )

    print(
        f"{category:<15}"
        f"low={low_score:6.2f}"
        f"  high={high_score:6.2f}"
    )

print("\nSize Score validation complete.")