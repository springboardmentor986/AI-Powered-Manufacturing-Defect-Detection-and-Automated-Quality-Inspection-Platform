from pathlib import Path

import cv2
import numpy as np
from sklearn.ensemble import IsolationForest


IMAGE_SIZE = (128, 128)


def preprocess_image(image_path: str):
    """
    OpenCV preprocessing pipeline:
    1. Read image
    2. Resize
    3. Noise reduction
    4. Contrast enhancement
    5. Edge extraction
    """

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read image")

    original_height, original_width = image.shape[:2]

    resized = cv2.resize(image, IMAGE_SIZE)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    denoised = cv2.GaussianBlur(gray, (5, 5), 0)

    enhanced = cv2.equalizeHist(denoised)

    edges = cv2.Canny(enhanced, 50, 150)

    return {
        "original": image,
        "resized": resized,
        "gray": gray,
        "denoised": denoised,
        "enhanced": enhanced,
        "edges": edges,
        "original_width": original_width,
        "original_height": original_height,
    }


def extract_features(image_path: str):
    """
    Extract compact numerical features using OpenCV + NumPy.
    """

    processed = preprocess_image(image_path)

    gray = processed["enhanced"]
    edges = processed["edges"]

    small_gray = cv2.resize(gray, (32, 32))
    small_edges = cv2.resize(edges, (32, 32))

    gray_features = (
        small_gray.astype(np.float32).flatten() / 255.0
    )

    edge_features = (
        small_edges.astype(np.float32).flatten() / 255.0
    )

    features = np.concatenate(
        [gray_features, edge_features]
    )

    return features


def calculate_image_quality(image_path: str):
    """
    Basic image-quality analysis.
    """

    processed = preprocess_image(image_path)

    gray = processed["gray"]

    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    blur_score = float(
        cv2.Laplacian(gray, cv2.CV_64F).var()
    )

    if blur_score < 50:
        sharpness_status = "Low"
    elif blur_score < 150:
        sharpness_status = "Medium"
    else:
        sharpness_status = "High"

    return {
        "width": processed["original_width"],
        "height": processed["original_height"],
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "sharpness_score": round(blur_score, 2),
        "sharpness": sharpness_status,
    }


def train_anomaly_model(category_path: str, model_path: str):
    """
    Train an Isolation Forest using MVTec AD train/good images.

    A validation-style threshold is calculated from the training
    distribution so that the detector is less aggressive than
    Isolation Forest's default contamination threshold.
    """

    train_dir = Path(category_path) / "train" / "good"

    if not train_dir.exists():
        raise ValueError(
            f"Training directory not found: {train_dir}"
        )

    image_files = list(train_dir.glob("*.png"))

    if not image_files:
        image_files = list(train_dir.glob("*.jpg"))

    if not image_files:
        image_files = list(train_dir.glob("*.jpeg"))

    if not image_files:
        raise ValueError(
            f"No training images found in {train_dir}"
        )

    features = []

    for image_file in image_files:
        try:
            feature = extract_features(str(image_file))
            features.append(feature)
        except Exception:
            continue

    if not features:
        raise ValueError(
            "Unable to extract training features"
        )

    X = np.array(features)

    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=-1
    )

    model.fit(X)

    # Calculate decision scores for known-good training images.
    training_scores = model.decision_function(X)

    # Keep approximately 2% of the lowest-scoring good samples
    # outside the accepted normal range.
    threshold = float(
        np.percentile(training_scores, 2)
    )

    import joblib

    model_package = {
        "model": model,
        "threshold": threshold,
        "training_images": len(features),
        "threshold_percentile": 2
    }

    Path(model_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        model_package,
        model_path
    )

    return {
        "category": Path(category_path).name,
        "training_images": len(features),
        "threshold": round(threshold, 6),
        "model_path": model_path,
    }


def detect_defect(
    image_path: str,
    model_path: str
):
    """
    Predict whether an image is anomalous using
    the calibrated category-specific threshold.
    """

    import joblib

    if not Path(model_path).exists():
        raise ValueError(
            "Model not trained for this category"
        )

    model_package = joblib.load(model_path)

    # Support the new calibrated model format.
    if isinstance(model_package, dict):
        model = model_package["model"]
        threshold = float(model_package["threshold"])
    else:
        # Backward compatibility for old models.
        model = model_package
        threshold = 0.0

    features = extract_features(image_path)

    feature_vector = features.reshape(1, -1)

    anomaly_score = float(
        model.decision_function(feature_vector)[0]
    )

    # Lower decision scores indicate stronger anomalies.
    is_defective = anomaly_score < threshold

    # Distance from the calibrated threshold.
    distance = abs(anomaly_score - threshold)

    confidence = min(
        99.0,
        max(
            50.0,
            50.0 + distance * 250.0
        )
    )

    return {
        "is_defective": bool(is_defective),
        "prediction": (
            "Defect Detected"
            if is_defective
            else "No Defect"
        ),
        "anomaly_score": round(
            anomaly_score,
            4
        ),
        "confidence": round(
            confidence,
            2
        ),
        "decision_threshold": round(
            threshold,
            4
        ),
    }