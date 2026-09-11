import os
import cv2
import joblib
import numpy as np

from pathlib import Path

from skimage.feature import hog, local_binary_pattern

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = BASE_DIR / "dataset" / "mvtec_ad" / "bottle"

MODEL_PATH = BASE_DIR / "backend" / "defect_model.pkl"
MODEL_INFO_PATH = BASE_DIR / "backend" / "defect_model_info.pkl"


# ============================================================
# DEFECT TYPES
# ============================================================

DEFECT_TYPES = {
    "good": "No Defect",
    "broken_large": "Broken Large",
    "broken_small": "Broken Small",
    "contamination": "Contamination"
}


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(image_path):
    """
    Extract HOG + HSV + LBP features.

    These features are used by the ML defect classifier.
    """

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    # Resize
    image = cv2.resize(
        image,
        (128, 128)
    )

    # Mild preprocessing
    image = cv2.GaussianBlur(
        image,
        (3, 3),
        0
    )

    # --------------------------------------------------------
    # HOG FEATURES
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    hog_features = hog(
        gray,
        orientations=9,
        pixels_per_cell=(8, 8),
        cells_per_block=(2, 2),
        block_norm="L2-Hys"
    )

    # --------------------------------------------------------
    # HSV COLOR FEATURES
    # --------------------------------------------------------

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    h_hist = cv2.calcHist(
        [hsv],
        [0],
        None,
        [32],
        [0, 180]
    ).flatten()

    s_hist = cv2.calcHist(
        [hsv],
        [1],
        None,
        [32],
        [0, 256]
    ).flatten()

    v_hist = cv2.calcHist(
        [hsv],
        [2],
        None,
        [32],
        [0, 256]
    ).flatten()

    h_hist = h_hist / (
        np.sum(h_hist) + 1e-8
    )

    s_hist = s_hist / (
        np.sum(s_hist) + 1e-8
    )

    v_hist = v_hist / (
        np.sum(v_hist) + 1e-8
    )

    color_features = np.concatenate([
        h_hist,
        s_hist,
        v_hist
    ])

    # --------------------------------------------------------
    # LBP TEXTURE FEATURES
    # --------------------------------------------------------

    lbp = local_binary_pattern(
        gray,
        P=16,
        R=2,
        method="uniform"
    )

    lbp_hist, _ = np.histogram(
        lbp.ravel(),
        bins=np.arange(0, 19),
        range=(0, 18)
    )

    lbp_hist = lbp_hist.astype(
        np.float32
    )

    lbp_hist = lbp_hist / (
        np.sum(lbp_hist) + 1e-8
    )

    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    features = np.concatenate([
        hog_features,
        color_features,
        lbp_hist
    ])

    return features.astype(
        np.float32
    )


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    X = []
    y = []

    # --------------------------------------------------------
    # GOOD IMAGES
    # --------------------------------------------------------

    good_path = (
        DATASET_PATH /
        "train" /
        "good"
    )

    # --------------------------------------------------------
    # DEFECT IMAGES
    # --------------------------------------------------------

    defect_paths = {
        "broken_large":
            DATASET_PATH /
            "test" /
            "broken_large",

        "broken_small":
            DATASET_PATH /
            "test" /
            "broken_small",

        "contamination":
            DATASET_PATH /
            "test" /
            "contamination"
    }

    print("=" * 65)
    print("VisionInspect AI - ML Defect Classifier")
    print("=" * 65)

    # --------------------------------------------------------
    # LOAD GOOD
    # --------------------------------------------------------

    if good_path.exists():

        files = list(
            good_path.glob("*.png")
        )

        print(
            f"\nGOOD              : {len(files)} images"
        )

        for image_path in files:

            try:

                features = extract_features(
                    image_path
                )

                X.append(features)
                y.append("good")

            except Exception as e:

                print(
                    f"Skipping {image_path.name}: {e}"
                )

    else:

        print(
            f"WARNING: {good_path} not found"
        )

    # --------------------------------------------------------
    # LOAD DEFECTS
    # --------------------------------------------------------

    for category, folder in defect_paths.items():

        if not folder.exists():

            print(
                f"WARNING: {folder} not found"
            )

            continue

        files = list(
            folder.glob("*.png")
        )

        print(
            f"{category:<20}: {len(files)} images"
        )

        for image_path in files:

            try:

                features = extract_features(
                    image_path
                )

                X.append(features)
                y.append(category)

            except Exception as e:

                print(
                    f"Skipping {image_path.name}: {e}"
                )

    if len(X) == 0:

        raise RuntimeError(
            "No images were found in the MVTec dataset."
        )

    X = np.array(X)
    y = np.array(y)

    print("\nTotal samples :", len(X))
    print("Feature size  :", X.shape[1])

    return X, y


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model():

    X, y = load_dataset()

    print("\nClass distribution:")

    unique, counts = np.unique(
        y,
        return_counts=True
    )

    for label, count in zip(
        unique,
        counts
    ):

        print(
            f"  {label:<20}: {count}"
        )

    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    print("\nTraining samples :", len(X_train))
    print("Testing samples  :", len(X_test))

    # --------------------------------------------------------
    # SVM MODEL
    # --------------------------------------------------------

    model = Pipeline([
        (
            "scaler",
            StandardScaler()
        ),

        (
            "classifier",
            SVC(
                kernel="rbf",
                C=10,
                gamma="scale",
                class_weight="balanced",
                probability=True,
                random_state=42
            )
        )
    ])

    print("\nTraining ML classifier...")

    model.fit(
        X_train,
        y_train
    )

    print("Training completed.")

    # --------------------------------------------------------
    # TEST
    # --------------------------------------------------------

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print("\n" + "=" * 65)
    print("MODEL EVALUATION")
    print("=" * 65)

    print(
        f"\nAccuracy: {accuracy * 100:.2f}%"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            predictions
        )
    )

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    joblib.dump(
        model,
        MODEL_PATH
    )

    model_info = {
        "model": "SVM",
        "kernel": "RBF",
        "features": [
            "HOG",
            "HSV Color Histogram",
            "LBP Texture"
        ],
        "classes": list(
            model.named_steps[
                "classifier"
            ].classes_
        ),
        "accuracy": float(
            accuracy
        ),
        "dataset": "MVTec AD Bottle",
        "image_size": "128x128"
    }

    joblib.dump(
        model_info,
        MODEL_INFO_PATH
    )

    print("\n" + "=" * 65)
    print("MODEL SAVED")
    print("=" * 65)

    print(
        f"\nModel file: {MODEL_PATH}"
    )

    print(
        f"Model info: {MODEL_INFO_PATH}"
    )

    print("\nClasses:")

    print(
        model.named_steps[
            "classifier"
        ].classes_
    )

    return model


# ============================================================
# DATASET GROUND-TRUTH CLASSIFIER
# ============================================================

def classify_defect(image_name):
    """
    Dataset ground-truth classifier.

    This is kept from the original project code.

    IMPORTANT:
    This function is ONLY for MVTec dataset paths.
    It is NOT used for real uploaded-image prediction.
    """

    image_path = Path(image_name)

    category = image_path.parent.name

    if category in DEFECT_TYPES:

        return {
            "defect_type":
                DEFECT_TYPES[category],

            "category":
                category
        }

    return {
        "defect_type":
            "Unknown",

        "category":
            "unknown"
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 65)
    print("VISIONINSPECT AI")
    print("DEFECT CLASSIFICATION MODULE")
    print("=" * 65)

    print("\nSupported defect types:")

    for category, name in DEFECT_TYPES.items():

        print(
            f"  {category:<20} -> {name}"
        )

    print(
        "\nStarting ML model training..."
    )

    train_model()

    print("\nDefect classification module ready.")
    print("=" * 65)