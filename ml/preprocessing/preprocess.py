import cv2
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

# MUST match the Autoencoder training/inference input size.
IMAGE_SIZE = (224, 224)


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(image):
    """
    Extract basic visual features from the preprocessed RGB image.

    Features:
    - Edge information
    - Mean intensity
    - Standard deviation
    - Sharpness
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    # Edge information
    edges = cv2.Canny(
        gray,
        100,
        200
    )

    # Intensity information
    mean_intensity = float(
        np.mean(gray)
    )

    std_intensity = float(
        np.std(gray)
    )

    # Sharpness using variance of Laplacian
    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    return {
        "edges": edges,
        "mean_intensity": mean_intensity,
        "std_intensity": std_intensity,
        "sharpness": sharpness
    }


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(input_path, output_path=None):
    """
    Complete preprocessing used by the Autoencoder.

    Pipeline:
        Read
        ↓
        Resize
        ↓
        BGR → RGB
        ↓
        Mild noise removal
        ↓
        Local contrast enhancement
        ↓
        Normalization [0, 1]
        ↓
        Feature extraction

    IMPORTANT:
    This same function must be used during:
        1. Autoencoder training
        2. Autoencoder validation/testing
        3. Threshold generation
        4. Final inference
    """

    # ========================================================
    # 1. READ IMAGE
    # ========================================================

    image = cv2.imread(
        str(input_path),
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise ValueError(
            f"Could not read image: {input_path}"
        )

    # ========================================================
    # 2. RESIZE
    # ========================================================

    image = cv2.resize(
        image,
        IMAGE_SIZE,
        interpolation=cv2.INTER_AREA
    )

    # ========================================================
    # 3. BGR → RGB
    # ========================================================

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    # ========================================================
    # 4. MILD NOISE REMOVAL
    # ========================================================
    # Bilateral filtering reduces noise while preserving
    # edges that are important for manufacturing defects.

    denoised = cv2.bilateralFilter(
        image,
        d=5,
        sigmaColor=30,
        sigmaSpace=30
    )

    # ========================================================
    # 5. CONTRAST / IMAGE ENHANCEMENT
    # ========================================================
    # CLAHE is applied only to the luminance channel so that
    # color information is preserved.

    lab = cv2.cvtColor(
        denoised,
        cv2.COLOR_RGB2LAB
    )

    l_channel, a_channel, b_channel = cv2.split(
        lab
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced_l = clahe.apply(
        l_channel
    )

    enhanced_lab = cv2.merge(
        [
            enhanced_l,
            a_channel,
            b_channel
        ]
    )

    enhanced = cv2.cvtColor(
        enhanced_lab,
        cv2.COLOR_LAB2RGB
    )

    # ========================================================
    # 6. NORMALIZATION
    # ========================================================

    normalized = (
        enhanced.astype(np.float32)
        / 255.0
    )

    # ========================================================
    # 7. FEATURE EXTRACTION
    # ========================================================

    features = extract_features(
        enhanced
    )

    # ========================================================
    # 8. SAVE PROCESSED IMAGE
    # ========================================================

    if output_path is not None:

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        processed = np.clip(
            normalized * 255.0,
            0,
            255
        ).astype(np.uint8)

        processed_bgr = cv2.cvtColor(
            processed,
            cv2.COLOR_RGB2BGR
        )

        success = cv2.imwrite(
            str(output_path),
            processed_bgr
        )

        if not success:
            raise IOError(
                f"Could not save image: "
                f"{output_path}"
            )

    # ========================================================
    # RETURN
    # ========================================================

    return normalized, features


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # Project structure:
    #
    # D:\VisionInspectAI\
    # └── ml\
    #     ├── dataset\
    #     ├── preprocessing\
    #     └── processed\

    ml_dir = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    dataset_dir = (
        ml_dir
        / "dataset"
    )

    output_dir = (
        ml_dir
        / "processed"
    )

    bottle_dir = (
        dataset_dir
        / "bottle"
        / "train"
        / "good"
    )

    if not bottle_dir.exists():

        raise FileNotFoundError(
            f"Training directory not found: "
            f"{bottle_dir}"
        )

    images = list(
        bottle_dir.glob("*.png")
    )

    if not images:

        raise FileNotFoundError(
            f"No training images found in "
            f"{bottle_dir}"
        )

    input_image = images[0]

    output_image = (
        output_dir
        / "bottle_sample.png"
    )

    normalized, features = preprocess_image(
        input_image,
        output_image
    )

    print()
    print("=" * 55)
    print("MVTec AD PREPROCESSING SUCCESS")
    print("=" * 55)

    print(
        f"Input image      : {input_image}"
    )

    print(
        f"Output image     : {output_image}"
    )

    print(
        f"Image size       : "
        f"{IMAGE_SIZE[0]} x {IMAGE_SIZE[1]}"
    )

    print(
        f"Pixel range      : "
        f"{normalized.min():.2f} - "
        f"{normalized.max():.2f}"
    )

    print(
        f"Data type        : "
        f"{normalized.dtype}"
    )

    print(
        f"Mean intensity   : "
        f"{features['mean_intensity']:.2f}"
    )

    print(
        f"Std intensity    : "
        f"{features['std_intensity']:.2f}"
    )

    print(
        f"Sharpness        : "
        f"{features['sharpness']:.2f}"
    )

    print(
        f"Feature shape    : "
        f"{features['edges'].shape}"
    )

    print(
        f"Training images  : "
        f"{len(images)}"
    )

    print("=" * 55)
