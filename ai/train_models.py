from pathlib import Path
import cv2
import numpy as np
import joblib

from sklearn.ensemble import IsolationForest


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path("datasets/mvtec_ad")
MODEL_DIR = Path("ai/models")

# Complete MVTec AD dataset
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


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def extract_features(image_path):
    """
    Preprocess one image and extract normalized features.

    Steps:
    1. Resize to 128x128
    2. Convert to grayscale
    3. Gaussian noise reduction
    4. Histogram equalization
    5. Canny edge detection
    6. Resize feature maps to 32x32
    7. Combine intensity + edge features
    """

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    # Resize
    image = cv2.resize(image, (128, 128))

    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Noise removal
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Contrast enhancement
    enhanced = cv2.equalizeHist(blurred)

    # Edge detection
    edges = cv2.Canny(enhanced, 50, 150)

    # Reduce feature size
    enhanced_small = cv2.resize(enhanced, (32, 32))
    edges_small = cv2.resize(edges, (32, 32))

    # Normalize
    enhanced_features = enhanced_small.astype(np.float32) / 255.0
    edge_features = edges_small.astype(np.float32) / 255.0

    # Combine features
    features = np.concatenate([
        enhanced_features.flatten(),
        edge_features.flatten()
    ])

    return features


# ============================================================
# LOAD TRAINING IMAGES
# ============================================================

def load_training_features(category):
    """
    Load defect-free training images from:

    datasets/mvtec_ad/<category>/train/good
    """

    train_dir = BASE_DIR / category / "train" / "good"

    if not train_dir.exists():
        raise FileNotFoundError(
            f"Training directory not found: {train_dir}"
        )

    image_files = sorted([
        p for p in train_dir.iterdir()
        if p.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp"]
    ])

    if not image_files:
        raise RuntimeError(
            f"No training images found in: {train_dir}"
        )

    print(f"Found {len(image_files)} training images.")

    features = []

    for index, image_path in enumerate(image_files, start=1):

        try:
            feature_vector = extract_features(image_path)
            features.append(feature_vector)

        except Exception as error:
            print(
                f"Warning: Could not process "
                f"{image_path.name}: {error}"
            )

        # Progress display
        if index % 50 == 0 or index == len(image_files):
            print(
                f"  Processed {index}/{len(image_files)} images"
            )

    if not features:
        raise RuntimeError(
            f"No valid features extracted for {category}"
        )

    return np.array(features, dtype=np.float32)


# ============================================================
# TRAIN ONE CATEGORY MODEL
# ============================================================

def train_category(category):

    print("\n" + "=" * 60)
    print(f"TRAINING CATEGORY: {category.upper()}")
    print("=" * 60)

    # Load features
    X = load_training_features(category)

    print(f"Feature matrix shape: {X.shape}")

    # Isolation Forest
    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=-1
    )

    print("Training Isolation Forest...")

    model.fit(X)

    # Calculate training anomaly scores
    training_scores = model.decision_function(X)

    # Use the 2nd percentile as the anomaly threshold
    threshold = float(
        np.percentile(training_scores, 2)
    )

    print(f"Training score minimum: {training_scores.min():.6f}")
    print(f"Training score maximum: {training_scores.max():.6f}")
    print(f"Anomaly threshold: {threshold:.6f}")

    # Create model directory
    category_model_dir = MODEL_DIR / category
    category_model_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save model
    model_path = category_model_dir / "isolation_forest.joblib"

    joblib.dump(
        model,
        model_path
    )

    # Save complete model package
    package = {
        "model": model,
        "threshold": threshold,
        "category": category,
        "training_images": len(X),
        "feature_size": X.shape[1],
        "threshold_percentile": 2
    }

    package_path = category_model_dir / "model_package.joblib"

    joblib.dump(
        package,
        package_path
    )

    print(f"Model saved: {model_path}")
    print(f"Package saved: {package_path}")

    return {
        "category": category,
        "images": len(X),
        "features": X.shape[1],
        "threshold": threshold
    }


# ============================================================
# TRAIN ALL 15 CATEGORIES
# ============================================================

def main():

    print("=" * 60)
    print("VISIONINSPECT AI")
    print("MVTec AD - 15 Category Model Training")
    print("=" * 60)

    print(f"\nDataset directory: {BASE_DIR}")
    print(f"Model directory: {MODEL_DIR}")
    print(f"Categories: {len(CATEGORIES)}")

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    for category in CATEGORIES:

        try:

            result = train_category(category)

            results.append(result)

        except Exception as error:

            print(
                f"\nERROR training {category}: {error}"
            )

    # ========================================================
    # TRAINING SUMMARY
    # ========================================================

    print("\n\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)

    print(
        f"{'Category':<15}"
        f"{'Images':<10}"
        f"{'Features':<12}"
        f"Threshold"
    )

    print("-" * 60)

    for result in results:

        print(
            f"{result['category']:<15}"
            f"{result['images']:<10}"
            f"{result['features']:<12}"
            f"{result['threshold']:.6f}"
        )

    print("-" * 60)

    print(
        f"Successfully trained: "
        f"{len(results)}/{len(CATEGORIES)} categories"
    )

    if len(results) == len(CATEGORIES):
        print("\nALL 15 MODELS TRAINED SUCCESSFULLY.")
    else:
        print(
            "\nWARNING: Some category models "
            "were not trained successfully."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()