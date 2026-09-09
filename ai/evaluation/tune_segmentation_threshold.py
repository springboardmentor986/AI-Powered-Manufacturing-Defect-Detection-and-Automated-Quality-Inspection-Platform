from pathlib import Path
import csv

import numpy as np
import torch

from ai.models.defect_segmenter import UNet
from ai.evaluation.segmentation_dataset import (
    MVTecSegmentationDataset,
)


# ============================================================
# Configuration
# ============================================================

SPLIT_FILE = Path(
    "ai/evaluation/segmentation_splits/validation.csv"
)

MODEL_PATH = Path(
    "ai/models/defect_segmenter_unet.pt"
)

IMAGE_SIZE = 224

THRESHOLDS = np.arange(
    0.10,
    0.91,
    0.05,
)


# ============================================================
# Device
# ============================================================

def get_device():

    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


# ============================================================
# Load samples
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
# Calculate segmentation metrics
# ============================================================

def calculate_metrics(
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

    # --------------------------------------------------------
    # Precision
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Recall
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # F1
    # --------------------------------------------------------

    if precision + recall == 0:

        f1 = 0.0

    else:

        f1 = (
            2 * precision * recall
            / (precision + recall)
        )

    # --------------------------------------------------------
    # IoU
    # --------------------------------------------------------

    union = np.logical_or(
        predictions,
        targets,
    ).sum()

    if union == 0:

        iou = 1.0

    else:

        iou = (
            true_positive / union
        )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou": iou,
    }


# ============================================================
# Main
# ============================================================

def main():

    print("U-Net Validation Threshold Tuning")

    device = get_device()

    print(
        f"\nUsing device: {device}"
    )

    # --------------------------------------------------------
    # Load validation dataset
    # --------------------------------------------------------

    samples = load_samples(
        SPLIT_FILE
    )

    dataset = MVTecSegmentationDataset(
        samples=samples,
        image_size=IMAGE_SIZE,
    )

    print(
        f"Validation samples: {len(dataset)}"
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = UNet(
        in_channels=3,
        out_channels=1,
    ).to(device)

    model.load_state_dict(
        torch.load(
            MODEL_PATH,
            map_location=device,
            weights_only=True,
        )
    )

    model.eval()

    print(
        f"Loaded model: {MODEL_PATH}"
    )

    # --------------------------------------------------------
    # Generate predictions
    # --------------------------------------------------------

    all_probabilities = []
    all_targets = []

    print(
        "\nGenerating validation predictions..."
    )

    with torch.no_grad():

        for index in range(len(dataset)):

            image, mask = dataset[index]

            image = image.unsqueeze(0).to(
                device
            )

            logits = model(image)

            probabilities = torch.sigmoid(
                logits
            )

            all_probabilities.append(
                probabilities.squeeze()
                .cpu()
                .numpy()
            )

            all_targets.append(
                mask.squeeze()
                .numpy()
            )

    probabilities = np.concatenate(
        [
            prediction.reshape(-1)
            for prediction in all_probabilities
        ]
    )

    targets = np.concatenate(
        [
            target.reshape(-1)
            for target in all_targets
        ]
    )

    print(
        f"Total validation pixels: "
        f"{len(targets):,}"
    )

    # --------------------------------------------------------
    # Test thresholds
    # --------------------------------------------------------

    results = []

    print(
        f"\n{'Threshold':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
        f"{'IoU':<12}"
        f"{'Pred Area %':<12}"
    )

    for threshold in THRESHOLDS:

        predictions = (
            probabilities >= threshold
        )

        metrics = calculate_metrics(
            predictions,
            targets,
        )

        predicted_area = (
            predictions.mean()
            * 100
        )

        results.append(
            {
                "threshold": float(threshold),
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "iou": metrics["iou"],
                "predicted_area_percentage": predicted_area,
            }
        )

        print(
            f"{threshold:<12.2f}"
            f"{metrics['precision']:<12.4f}"
            f"{metrics['recall']:<12.4f}"
            f"{metrics['f1']:<12.4f}"
            f"{metrics['iou']:<12.4f}"
            f"{predicted_area:<12.2f}"
        )

    # --------------------------------------------------------
    # Find best threshold
    # --------------------------------------------------------

    best_result = max(
        results,
        key=lambda result: result["f1"],
    )

    print("\nBest Validation Threshold:")

    print(
        f"Threshold : "
        f"{best_result['threshold']:.2f}"
    )

    print(
        f"Precision : "
        f"{best_result['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{best_result['recall']:.4f}"
    )

    print(
        f"F1        : "
        f"{best_result['f1']:.4f}"
    )

    print(
        f"IoU       : "
        f"{best_result['iou']:.4f}"
    )

    print(
        f"Pred area : "
        f"{best_result['predicted_area_percentage']:.2f}%"
    )

    # --------------------------------------------------------
    # Save selected threshold
    # --------------------------------------------------------

    output_path = Path(
        "ai/models/segmentation_threshold.txt"
    )

    output_path.write_text(
        f"{best_result['threshold']:.4f}\n",
        encoding="utf-8",
    )

    print(
        f"\nSaved threshold → {output_path}"
    )


if __name__ == "__main__":
    main()