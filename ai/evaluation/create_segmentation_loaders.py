from pathlib import Path
import csv

from torch.utils.data import DataLoader

from ai.evaluation.segmentation_dataset import (
    MVTecSegmentationDataset,
)


# ============================================================
# Configuration
# ============================================================

SPLIT_DIRECTORY = Path(
    "ai/evaluation/segmentation_splits"
)

BATCH_SIZE = 8


# ============================================================
# Load CSV
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
# Create DataLoaders
# ============================================================

def create_dataloaders():

    train_samples = load_samples(
        SPLIT_DIRECTORY / "train.csv"
    )

    validation_samples = load_samples(
        SPLIT_DIRECTORY / "validation.csv"
    )

    test_samples = load_samples(
        SPLIT_DIRECTORY / "test.csv"
    )

    # --------------------------------------------------------
    # Datasets
    # --------------------------------------------------------

    train_dataset = MVTecSegmentationDataset(
        train_samples,
        image_size=224,
    )

    validation_dataset = MVTecSegmentationDataset(
        validation_samples,
        image_size=224,
    )

    test_dataset = MVTecSegmentationDataset(
        test_samples,
        image_size=224,
    )

    # --------------------------------------------------------
    # DataLoaders
    # --------------------------------------------------------

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
    )

    return (
        train_loader,
        validation_loader,
        test_loader,
    )


# ============================================================
# Test
# ============================================================

def main():

    (
        train_loader,
        validation_loader,
        test_loader,
    ) = create_dataloaders()

    print(
        "Training samples   :",
        len(train_loader.dataset),
    )

    print(
        "Validation samples :",
        len(validation_loader.dataset),
    )

    print(
        "Test samples       :",
        len(test_loader.dataset),
    )

    print()

    # Take one training batch
    images, masks = next(iter(train_loader))

    print(
        "Batch image shape:",
        images.shape,
    )

    print(
        "Batch mask shape :",
        masks.shape,
    )

    print(
        "Image dtype:",
        images.dtype,
    )

    print(
        "Mask dtype:",
        masks.dtype,
    )

    print(
        "Number of batches:",
        len(train_loader),
    )


if __name__ == "__main__":
    main()