from pathlib import Path
import random
import csv


# ============================================================
# Configuration
# ============================================================

DATASET_ROOT = Path("mvtec_anomaly_detection")

OUTPUT_DIRECTORY = Path("ai/evaluation/segmentation_splits")

RANDOM_SEED = 42

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


# ============================================================
# Find image + mask pairs
# ============================================================

def collect_samples():
    samples = []

    categories = sorted(
        category.name
        for category in DATASET_ROOT.iterdir()
        if category.is_dir()
    )

    for category in categories:

        test_directory = (
            DATASET_ROOT
            / category
            / "test"
        )

        ground_truth_directory = (
            DATASET_ROOT
            / category
            / "ground_truth"
        )

        if not test_directory.exists():
            continue

        # Every directory inside test/ represents a defect type.
        defect_directories = sorted(
            directory
            for directory in test_directory.iterdir()
            if directory.is_dir()
            and directory.name != "good"
        )

        for defect_directory in defect_directories:

            defect_type = defect_directory.name

            mask_directory = (
                ground_truth_directory
                / defect_type
            )

            for image_path in sorted(
                defect_directory.glob("*.png")
            ):

                mask_path = (
                    mask_directory
                    / f"{image_path.stem}_mask.png"
                )

                if not mask_path.exists():
                    print(
                        f"WARNING: Missing mask for "
                        f"{image_path}"
                    )
                    continue

                samples.append(
                    {
                        "category": category,
                        "defect_type": defect_type,
                        "image_path": str(image_path),
                        "mask_path": str(mask_path),
                    }
                )

    return samples


# ============================================================
# Split samples
# ============================================================

def split_samples(samples):

    random.seed(RANDOM_SEED)

    # Group by category + defect type.
    groups = {}

    for sample in samples:

        key = (
            sample["category"],
            sample["defect_type"],
        )

        groups.setdefault(key, []).append(sample)

    train_samples = []
    validation_samples = []
    test_samples = []

    for key in sorted(groups):

        group = groups[key]

        random.shuffle(group)

        total = len(group)

        train_count = int(
            total * TRAIN_RATIO
        )

        validation_count = int(
            total * VALIDATION_RATIO
        )

        train_group = group[
            :train_count
        ]

        validation_group = group[
            train_count:
            train_count + validation_count
        ]

        test_group = group[
            train_count + validation_count:
        ]

        train_samples.extend(train_group)
        validation_samples.extend(validation_group)
        test_samples.extend(test_group)

        print(
            f"{key[0]:12s} | "
            f"{key[1]:20s} | "
            f"total={total:3d} | "
            f"train={len(train_group):3d} | "
            f"val={len(validation_group):3d} | "
            f"test={len(test_group):3d}"
        )

    return (
        train_samples,
        validation_samples,
        test_samples,
    )


# ============================================================
# Save CSV
# ============================================================

def save_split(samples, filename):

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIRECTORY
        / filename
    )

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "category",
                "defect_type",
                "image_path",
                "mask_path",
            ],
        )

        writer.writeheader()

        writer.writerows(samples)

    print(
        f"\nSaved {len(samples)} samples → "
        f"{output_path}"
    )


# ============================================================
# Main
# ============================================================

def main():

    print("MVTec Segmentation Dataset Preparation")

    samples = collect_samples()

    print(
        f"\nTotal defective image/mask pairs: "
        f"{len(samples)}"
    )

    (
        train_samples,
        validation_samples,
        test_samples,
    ) = split_samples(samples)

    print("\nFinal Split:")

    print(
        f"Training   : {len(train_samples)}"
    )

    print(
        f"Validation : {len(validation_samples)}"
    )

    print(
        f"Test       : {len(test_samples)}"
    )

    total = (
        len(train_samples)
        + len(validation_samples)
        + len(test_samples)
    )

    print(
        f"Total      : {total}"
    )

    save_split(
        train_samples,
        "train.csv",
    )

    save_split(
        validation_samples,
        "validation.csv",
    )

    save_split(
        test_samples,
        "test.csv",
    )


if __name__ == "__main__":
    main()