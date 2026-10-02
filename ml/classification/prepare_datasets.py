from pathlib import Path
import shutil
import random


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"

OUTPUT_DIR = BASE_DIR / "classification" / "dataset"


# ============================================================
# SETTINGS
# ============================================================

RANDOM_SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


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
    "zipper"
]


# ============================================================
# RANDOM GENERATOR
# ============================================================

random.seed(RANDOM_SEED)


# ============================================================
# GET IMAGES
# ============================================================

def get_images(folder):

    images = []

    if not folder.exists():
        return images

    for file in folder.iterdir():

        if (
            file.is_file()
            and file.suffix.lower() in IMAGE_EXTENSIONS
        ):
            images.append(file)

    return sorted(images)


# ============================================================
# SPLIT IMAGES
# ============================================================

def split_images(images):

    images = images.copy()

    random.shuffle(images)

    total = len(images)

    train_count = int(total * TRAIN_RATIO)

    val_count = int(total * VAL_RATIO)

    train_images = images[:train_count]

    val_images = images[
        train_count:
        train_count + val_count
    ]

    test_images = images[
        train_count + val_count:
    ]

    return (
        train_images,
        val_images,
        test_images
    )


# ============================================================
# COPY IMAGES
# ============================================================

def copy_images(
    images,
    destination,
    category,
    defect_class,
    split
):

    destination.mkdir(
        parents=True,
        exist_ok=True
    )

    for index, image in enumerate(images):

        # Add category/class/index to avoid filename collisions
        new_name = (
            f"{category}_"
            f"{defect_class}_"
            f"{index:04d}"
            f"{image.suffix.lower()}"
        )

        destination_file = (
            destination / new_name
        )

        shutil.copy2(
            image,
            destination_file
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("VISIONINSPECT AI")
    print("DEFECT CLASSIFICATION DATASET PREPARATION")
    print("=" * 70)

    print()
    print(f"Source      : {DATASET_DIR}")
    print(f"Output      : {OUTPUT_DIR}")
    print(f"Random seed : {RANDOM_SEED}")

    # --------------------------------------------------------
    # REMOVE OLD PREPARED DATASET
    # --------------------------------------------------------

    if OUTPUT_DIR.exists():

        print()
        print("Removing previous prepared dataset...")

        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    total_images = 0

    # ========================================================
    # PROCESS EACH CATEGORY
    # ========================================================

    for category_index, category in enumerate(
        CATEGORIES,
        start=1
    ):

        print()
        print("=" * 70)
        print(
            f"[{category_index}/"
            f"{len(CATEGORIES)}] "
            f"{category.upper()}"
        )
        print("=" * 70)

        source_test_dir = (
            DATASET_DIR /
            category /
            "test"
        )

        if not source_test_dir.exists():

            print(
                f"WARNING: Test folder not found:"
            )

            print(source_test_dir)

            continue

        category_total = 0

        # ----------------------------------------------------
        # FIND DEFECT CLASSES
        # ----------------------------------------------------

        defect_folders = []

        for folder in sorted(
            source_test_dir.iterdir()
        ):

            if not folder.is_dir():
                continue

            if folder.name.lower() == "good":
                continue

            defect_folders.append(folder)

        # ----------------------------------------------------
        # PROCESS EACH DEFECT CLASS
        # ----------------------------------------------------

        for defect_folder in defect_folders:

            defect_class = defect_folder.name

            images = get_images(
                defect_folder
            )

            if not images:

                print(
                    f"{defect_class:<25} "
                    f"0 images - skipped"
                )

                continue

            (
                train_images,
                val_images,
                test_images
            ) = split_images(images)

            # ------------------------------------------------
            # DESTINATION PATHS
            # ------------------------------------------------

            train_dir = (
                OUTPUT_DIR /
                category /
                "train" /
                defect_class
            )

            val_dir = (
                OUTPUT_DIR /
                category /
                "val" /
                defect_class
            )

            test_dir = (
                OUTPUT_DIR /
                category /
                "test" /
                defect_class
            )

            # ------------------------------------------------
            # COPY
            # ------------------------------------------------

            copy_images(
                train_images,
                train_dir,
                category,
                defect_class,
                "train"
            )

            copy_images(
                val_images,
                val_dir,
                category,
                defect_class,
                "val"
            )

            copy_images(
                test_images,
                test_dir,
                category,
                defect_class,
                "test"
            )

            # ------------------------------------------------
            # DISPLAY
            # ------------------------------------------------

            print(
                f"{defect_class:<25} "
                f"total={len(images):3d}  "
                f"train={len(train_images):3d}  "
                f"val={len(val_images):3d}  "
                f"test={len(test_images):3d}"
            )

            category_total += len(images)

        print()
        print(
            f"{category.upper()} TOTAL: "
            f"{category_total} images"
        )

        total_images += category_total

    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print("=" * 70)
    print("DATASET PREPARATION COMPLETED")
    print("=" * 70)

    print()
    print(
        f"Total images copied: "
        f"{total_images}"
    )

    print()
    print(
        f"Prepared dataset:"
    )

    print(OUTPUT_DIR)

    print()
    print("Structure:")
    print(
        "classification/dataset/"
        "<category>/"
        "train|val|test/"
        "<defect_class>/"
    )

    print()
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()