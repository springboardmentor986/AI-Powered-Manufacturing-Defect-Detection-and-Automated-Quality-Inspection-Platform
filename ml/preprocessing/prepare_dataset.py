from pathlib import Path

from PIL import Image
import numpy as np


# ==========================================
# CONFIGURATION
# ==========================================

IMAGE_SIZE = (224, 224)


# ==========================================
# PATHS
# ==========================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DATASET_DIR = (
    PROJECT_ROOT
    / "ml"
    / "dataset"
    / "bottle"
)

TRAIN_DIR = (
    DATASET_DIR
    / "train"
    / "good"
)

TEST_DIR = (
    DATASET_DIR
    / "test"
)


# ==========================================
# LOAD IMAGE
# ==========================================

def load_image(image_path):

    image = Image.open(
        image_path
    ).convert("RGB")

    image = image.resize(
        IMAGE_SIZE
    )

    image_array = np.asarray(
        image,
        dtype=np.float32
    ) / 255.0

    return image_array


# ==========================================
# LOAD TRAINING DATA
# ==========================================

def load_training_images():

    images = []

    image_paths = sorted(
        TRAIN_DIR.glob("*.png")
    )

    if not image_paths:
        raise FileNotFoundError(
            f"No training images found in {TRAIN_DIR}"
        )

    for image_path in image_paths:

        image = load_image(
            image_path
        )

        images.append(image)

    return np.array(images)


# ==========================================
# LOAD TEST DATA
# ==========================================

def load_test_images():

    images = []
    labels = []

    # ------------------------------
    # GOOD IMAGES
    # ------------------------------

    good_dir = (
        TEST_DIR
        / "good"
    )

    for image_path in sorted(
        good_dir.glob("*.png")
    ):

        images.append(
            load_image(image_path)
        )

        labels.append(0)


    # ------------------------------
    # DEFECT IMAGES
    # ------------------------------

    defect_types = [
        "broken_large",
        "broken_small",
        "contamination"
    ]

    for defect_type in defect_types:

        defect_dir = (
            TEST_DIR
            / defect_type
        )

        for image_path in sorted(
            defect_dir.glob("*.png")
        ):

            images.append(
                load_image(image_path)
            )

            labels.append(1)

    return (
        np.array(images),
        np.array(labels)
    )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    print()
    print("================================")
    print("MVTec AD DATASET PREPARATION")
    print("================================")

    print(
        f"Dataset: {DATASET_DIR}"
    )

    # Load training images
    train_images = (
        load_training_images()
    )

    print(
        f"Training images: "
        f"{len(train_images)}"
    )

    print(
        f"Training shape: "
        f"{train_images.shape}"
    )

    # Load test images
    test_images, test_labels = (
        load_test_images()
    )

    print(
        f"Test images: "
        f"{len(test_images)}"
    )

    print(
        f"Test shape: "
        f"{test_images.shape}"
    )

    print(
        f"Good test images: "
        f"{np.sum(test_labels == 0)}"
    )

    print(
        f"Defect test images: "
        f"{np.sum(test_labels == 1)}"
    )

    print()
    print("Dataset preparation successful!")
    print("================================")