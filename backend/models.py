# ============================================================
# VISIONINSPECT AI
# 4-CLASS DEFECT CLASSIFICATION MODEL
#
# Classes:
#   good
#   broken_large
#   broken_small
#   contamination
#
# Feature extraction:
#   HOG + HSV Color Histogram + LBP Texture
#
# Classifier:
#   SVM (RBF Kernel)
#
# ============================================================

from pathlib import Path

import cv2
import joblib
import numpy as np

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
# CONFIGURATION
# ============================================================

DATASET_DIR = Path(
    "dataset/mvtec_ad/bottle"
)

MODEL_PATH = Path(
    "backend/defect_model.pkl"
)

IMAGE_SIZE = (128, 128)

RANDOM_STATE = 42


# ============================================================
# CLASS DEFINITIONS
# ============================================================

CLASS_NAMES = [

    "good",

    "broken_large",

    "broken_small",

    "contamination"

]


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(image_path):
    """
    Extract combined visual features.

    Features:
        1. HOG       -> shape / edge information
        2. HSV hist  -> color information
        3. LBP       -> texture information
    """

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise ValueError(
            f"Unable to read image: {image_path}"
        )


    # --------------------------------------------------------
    # Resize
    # --------------------------------------------------------

    image = cv2.resize(
        image,
        IMAGE_SIZE,
        interpolation=cv2.INTER_AREA
    )


    # --------------------------------------------------------
    # Mild denoising
    # --------------------------------------------------------

    image = cv2.GaussianBlur(
        image,
        (3, 3),
        0
    )


    # ========================================================
    # 1. HOG FEATURES
    # ========================================================

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray_float = (
        gray.astype(np.float32) / 255.0
    )

    hog_features = hog(

        gray_float,

        orientations=9,

        pixels_per_cell=(8, 8),

        cells_per_block=(2, 2),

        block_norm="L2-Hys",

        feature_vector=True

    )


    # ========================================================
    # 2. HSV COLOR HISTOGRAM
    # ========================================================

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    color_features = []

    # H channel
    hist_h = cv2.calcHist(
        [hsv],
        [0],
        None,
        [32],
        [0, 180]
    )

    # S channel
    hist_s = cv2.calcHist(
        [hsv],
        [1],
        None,
        [32],
        [0, 256]
    )

    # V channel
    hist_v = cv2.calcHist(
        [hsv],
        [2],
        None,
        [32],
        [0, 256]
    )


    # Normalize histograms

    hist_h = cv2.normalize(
        hist_h,
        hist_h
    ).flatten()

    hist_s = cv2.normalize(
        hist_s,
        hist_s
    ).flatten()

    hist_v = cv2.normalize(
        hist_v,
        hist_v
    ).flatten()


    color_features.extend(
        hist_h
    )

    color_features.extend(
        hist_s
    )

    color_features.extend(
        hist_v
    )

    color_features = np.array(
        color_features,
        dtype=np.float32
    )


    # ========================================================
    # 3. LBP TEXTURE FEATURES
    # ========================================================

    radius = 2

    points = 16

    lbp = local_binary_pattern(
        gray,
        points,
        radius,
        method="uniform"
    )


    n_bins = points + 2

    lbp_hist, _ = np.histogram(

        lbp.ravel(),

        bins=np.arange(
            0,
            n_bins + 1
        ),

        range=(
            0,
            n_bins
        )

    )


    lbp_hist = (
        lbp_hist.astype(
            np.float32
        )
        /
        (lbp_hist.sum() + 1e-8)
    )


    # ========================================================
    # COMBINE FEATURES
    # ========================================================

    features = np.concatenate(

        [

            hog_features,

            color_features,

            lbp_hist

        ]

    )


    return features.astype(
        np.float32
    )


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    X = []

    y = []

    print()
    print("=" * 70)
    print("LOADING MVTEC AD BOTTLE DATASET")
    print("=" * 70)


    # --------------------------------------------------------
    # GOOD IMAGES
    # --------------------------------------------------------

    good_dir = (
        DATASET_DIR /
        "train" /
        "good"
    )

    good_files = sorted(
        good_dir.glob("*.png")
    )

    print()
    print(
        f"GOOD images found: {len(good_files)}"
    )


    for image_path in good_files:

        try:

            features = extract_features(
                image_path
            )

            X.append(
                features
            )

            y.append(
                "good"
            )

        except Exception as error:

            print(
                f"Skipping {image_path}: {error}"
            )


    # --------------------------------------------------------
    # DEFECTIVE CLASSES
    # --------------------------------------------------------

    test_dir = (
        DATASET_DIR /
        "test"
    )


    for class_name in [

        "broken_large",

        "broken_small",

        "contamination"

    ]:

        class_dir = (
            test_dir /
            class_name
        )

        files = sorted(
            class_dir.glob("*.png")
        )


        print(
            f"{class_name} images found: {len(files)}"
        )


        for image_path in files:

            try:

                features = extract_features(
                    image_path
                )

                X.append(
                    features
                )

                y.append(
                    class_name
                )

            except Exception as error:

                print(
                    f"Skipping {image_path}: {error}"
                )


    X = np.array(
        X,
        dtype=np.float32
    )

    y = np.array(
        y
    )


    print()
    print(
        f"Total images loaded: {len(X)}"
    )

    print(
        f"Feature vector size: {X.shape[1]}"
    )


    return X, y


# ============================================================
# MAIN TRAINING
# ============================================================

def main():

    print()
    print("=" * 70)
    print("VISIONINSPECT AI - DEFECT CLASSIFIER TRAINING")
    print("=" * 70)


    # ========================================================
    # LOAD DATA
    # ========================================================

    X, y = load_dataset()


    if len(X) == 0:

        raise RuntimeError(
            "No images were found."
        )


    # ========================================================
    # DATASET DISTRIBUTION
    # ========================================================

    print()
    print("=" * 70)
    print("DATASET DISTRIBUTION")
    print("=" * 70)


    for class_name in CLASS_NAMES:

        count = np.sum(
            y == class_name
        )

        print(
            f"{class_name:20s}: {count}"
        )


    # ========================================================
    # TRAIN / TEST SPLIT
    # ========================================================

    X_train, X_test, y_train, y_test = (
        train_test_split(

            X,
            y,

            test_size=0.25,

            random_state=RANDOM_STATE,

            stratify=y

        )
    )


    print()
    print(
        f"Training samples: {len(X_train)}"
    )

    print(
        f"Testing samples:  {len(X_test)}"
    )


    # ========================================================
    # MODEL
    # ========================================================

    print()
    print("=" * 70)
    print("TRAINING SVM CLASSIFIER")
    print("=" * 70)


    model = Pipeline(

        [

            (
                "scaler",

                StandardScaler()
            ),

            (
                "classifier",

                SVC(

                    kernel="rbf",

                    C=10.0,

                    gamma="scale",

                    class_weight="balanced",

                    probability=True,

                    random_state=RANDOM_STATE

                )

            )

        ]

    )


    # ========================================================
    # TRAIN
    # ========================================================

    model.fit(
        X_train,
        y_train
    )


    print()
    print(
        "Training completed."
    )


    # ========================================================
    # TEST
    # ========================================================

    y_pred = model.predict(
        X_test
    )


    accuracy = accuracy_score(
        y_test,
        y_pred
    )


    print()
    print("=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)


    print()
    print(
        f"Accuracy: {accuracy * 100:.2f}%"
    )


    # ========================================================
    # CLASSIFICATION REPORT
    # ========================================================

    print()
    print(
        "Classification Report:"
    )

    print()

    print(
        classification_report(

            y_test,

            y_pred,

            labels=CLASS_NAMES,

            target_names=CLASS_NAMES,

            zero_division=0

        )
    )


    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    matrix = confusion_matrix(

        y_test,

        y_pred,

        labels=CLASS_NAMES

    )


    print()
    print(
        "Confusion Matrix:"
    )

    print()

    print(
        "Rows = Actual"
    )

    print(
        "Columns = Predicted"
    )

    print()

    print(
        "              " +
        " ".join(
            f"{name:18s}"
            for name in CLASS_NAMES
        )
    )


    for index, class_name in enumerate(
        CLASS_NAMES
    ):

        values = matrix[index]

        print(

            f"{class_name:18s}"
            +
            " ".join(
                f"{value:<18d}"
                for value in values
            )

        )


    # ========================================================
    # SAVE MODEL
    # ========================================================

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    joblib.dump(

        model,

        MODEL_PATH

    )


    print()
    print("=" * 70)

    print(
        f"MODEL SAVED:"
    )

    print(
        MODEL_PATH
    )

    print("=" * 70)


    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    model_info = {

        "model_type":
            "SVM RBF",

        "feature_type":
            "HOG + HSV Histogram + LBP",

        "classes":
            CLASS_NAMES,

        "image_size":
            IMAGE_SIZE,

        "accuracy":
            float(accuracy),

        "random_state":
            RANDOM_STATE

    }


    info_path = Path(
        "backend/defect_model_info.pkl"
    )


    joblib.dump(
        model_info,
        info_path
    )


    print()
    print(
        "Model information saved."
    )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()