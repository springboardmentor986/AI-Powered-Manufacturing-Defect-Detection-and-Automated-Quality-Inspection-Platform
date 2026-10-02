import os
import json
import random
import sys

import cv2
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from preprocessing.preprocess import preprocess_image

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "saved_models")
THRESHOLD_FILE = os.path.join(BASE_DIR, "inference", "thresholds.json")

IMAGE_SIZE = (224, 224)

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

RANDOM_SEED = 42

# Percentage of normal training errors used as candidates.
# We test several percentiles and then choose the one
# giving the best validation F1.
NORMAL_PERCENTILES = [
    90,
    92,
    94,
    95,
    96,
    97,
    98,
    99,
    99.5,
]

TEST_VALIDATION_RATIO = 0.50

# Inspection must not silently accept known defective samples. Threshold
# calibration therefore prioritizes defect recall over normal-image precision.
MIN_DEFECT_RECALL = 1.0


# ============================================================
# RANDOM SEED
# ============================================================

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# AUTOENCODER
# SAME ARCHITECTURE USED DURING TRAINING
# ============================================================

class ConvAutoencoder(nn.Module):

    def __init__(self):

        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(
                256,
                128,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1,
            ),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(
                128,
                64,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1,
            ),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(
                64,
                32,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1,
            ),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(
                32,
                3,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1,
            ),
            nn.Sigmoid(),
        )

    def forward(self, x):

        encoded = self.encoder(x)
        decoded = self.decoder(encoded)

        return decoded


# ============================================================
# LOAD IMAGE
# IMPORTANT:
# EXACTLY SAME PREPROCESSING AS AE TRAINING
# ============================================================

def load_image(image_path):
    normalized, _ = preprocess_image(image_path)
    if normalized.shape != (IMAGE_SIZE[1], IMAGE_SIZE[0], 3):
        raise ValueError(f"Unexpected preprocessed shape: {normalized.shape}")

    tensor = np.transpose(normalized, (2, 0, 1))
    return torch.from_numpy(tensor).float().unsqueeze(0).to(DEVICE)


# ============================================================
# RECONSTRUCTION ERROR
# ============================================================

def reconstruction_error(model, image_path):

    image = load_image(image_path)

    with torch.no_grad():

        reconstructed = model(image)

        error = torch.mean(
            (image - reconstructed) ** 2
        ).item()

    return error


# ============================================================
# LOAD MODEL
# ============================================================

def load_model(category):

    model_path = os.path.join(
        MODEL_DIR,
        f"{category}_autoencoder.pth"
    )

    if not os.path.exists(model_path):

        raise FileNotFoundError(
            f"Model not found:\n{model_path}"
        )

    model = ConvAutoencoder().to(DEVICE)

    checkpoint = torch.load(
        model_path,
        map_location=DEVICE,
        weights_only=False,
    )

    if isinstance(checkpoint, dict):

        if "model_state_dict" in checkpoint:

            model.load_state_dict(
                checkpoint["model_state_dict"]
            )

        elif "state_dict" in checkpoint:

            model.load_state_dict(
                checkpoint["state_dict"]
            )

        else:

            model.load_state_dict(checkpoint)

    else:

        model.load_state_dict(checkpoint)

    model.eval()

    return model


# ============================================================
# TRAINING GOOD ERRORS
# ============================================================

def collect_training_good_errors(model, category):

    folder = os.path.join(
        DATASET_DIR,
        category,
        "train",
        "good",
    )

    if not os.path.exists(folder):

        raise FileNotFoundError(
            f"Training good folder not found:\n{folder}"
        )

    image_files = sorted([
        f
        for f in os.listdir(folder)
        if f.lower().endswith(
            (".png", ".jpg", ".jpeg", ".bmp")
        )
    ])

    errors = []

    for filename in image_files:

        path = os.path.join(
            folder,
            filename
        )

        try:

            error = reconstruction_error(
                model,
                path
            )

            errors.append(error)

        except Exception as e:

            print(
                f"Warning: failed {path}: {e}"
            )

    return np.array(
        errors,
        dtype=np.float32
    )


# ============================================================
# TEST DATA
#
# GOOD  -> label 0
# DEFECT -> label 1
# ============================================================

def collect_test_scores(model, category):

    test_dir = os.path.join(
        DATASET_DIR,
        category,
        "test",
    )

    if not os.path.exists(test_dir):

        raise FileNotFoundError(
            f"Test folder not found:\n{test_dir}"
        )

    scores = []
    labels = []
    filenames = []

    # --------------------------------------------------------
    # GOOD
    # --------------------------------------------------------

    good_dir = os.path.join(
        test_dir,
        "good"
    )

    if os.path.exists(good_dir):

        good_files = sorted([
            f
            for f in os.listdir(good_dir)
            if f.lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp")
            )
        ])

        for filename in good_files:

            path = os.path.join(
                good_dir,
                filename
            )

            try:

                error = reconstruction_error(
                    model,
                    path
                )

                scores.append(error)
                labels.append(0)
                filenames.append(path)

            except Exception as e:

                print(
                    f"Warning: failed {path}: {e}"
                )

    # --------------------------------------------------------
    # DEFECTS
    # --------------------------------------------------------

    defect_folders = sorted([
        folder
        for folder in os.listdir(test_dir)
        if os.path.isdir(
            os.path.join(test_dir, folder)
        )
        and folder != "good"
    ])

    for defect_type in defect_folders:

        defect_dir = os.path.join(
            test_dir,
            defect_type
        )

        defect_files = sorted([
            f
            for f in os.listdir(defect_dir)
            if f.lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp")
            )
        ])

        for filename in defect_files:

            path = os.path.join(
                defect_dir,
                filename
            )

            try:

                error = reconstruction_error(
                    model,
                    path
                )

                scores.append(error)
                labels.append(1)
                filenames.append(path)

            except Exception as e:

                print(
                    f"Warning: failed {path}: {e}"
                )

    return (
        np.array(scores, dtype=np.float32),
        np.array(labels, dtype=np.int32),
        filenames,
    )


# ============================================================
# THRESHOLD FROM NORMAL DISTRIBUTION
# ============================================================

def percentile_threshold(
    normal_errors,
    percentile
):

    return float(
        np.percentile(
            normal_errors,
            percentile
        )
    )


# ============================================================
# EVALUATE THRESHOLD
# ============================================================

def evaluate_threshold(
    scores,
    labels,
    threshold
):

    predictions = (
        scores >= threshold
    ).astype(int)

    accuracy = accuracy_score(
        labels,
        predictions
    )

    precision = precision_score(
        labels,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        labels,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        labels,
        predictions,
        zero_division=0
    )

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


# ============================================================
# FIND BEST NORMAL-DISTRIBUTION THRESHOLD
# ============================================================

def find_best_threshold(
    normal_errors,
    calibration_scores,
    calibration_labels,
):

    candidates = []

    # --------------------------------------------------------
    # Percentile thresholds
    # --------------------------------------------------------

    for percentile in NORMAL_PERCENTILES:

        threshold = percentile_threshold(
            normal_errors,
            percentile
        )

        candidates.append(
            (
                f"normal_p{percentile}",
                threshold
            )
        )

    # --------------------------------------------------------
    # Also test thresholds from validation data.
    # This allows the validation set to select a threshold
    # when the percentile candidates are not enough.
    # --------------------------------------------------------

    minimum = float(np.min(calibration_scores))

    maximum = float(np.max(calibration_scores))

    if minimum < maximum:

        validation_candidates = np.linspace(
            minimum,
            maximum,
            200
        )

        for threshold in validation_candidates:

            candidates.append(
                (
                    "validation",
                    float(threshold)
                )
            )

    # --------------------------------------------------------
    # Evaluate candidates
    # --------------------------------------------------------

    best = None

    for source, threshold in candidates:

        metrics = evaluate_threshold(
            calibration_scores,
            calibration_labels,
            threshold
        )

        # ----------------------------------------------------
        # Defect recall is a hard requirement. Among thresholds that meet it,
        # prefer precision, then F1, then the higher threshold.
        if metrics["recall"] < MIN_DEFECT_RECALL:
            continue

        current_key = (
            metrics["precision"],
            metrics["f1"],
            threshold,
        )

        if best is None:

            best = {
                "source": source,
                "threshold": threshold,
                "metrics": metrics,
            }

        else:

            best_key = (
                best["metrics"]["precision"],
                best["metrics"]["f1"],
                best["threshold"],
            )

            if current_key > best_key:

                best = {
                    "source": source,
                    "threshold": threshold,
                    "metrics": metrics,
                }

    if best is None:
        raise RuntimeError(
            "Unable to find a threshold meeting the required defect recall "
            f"of {MIN_DEFECT_RECALL:.0%}"
        )

    return best


# ============================================================
# SPLIT TEST DATA
# ============================================================

def split_test_data(
    scores,
    labels,
    filenames
):

    indices = np.arange(
        len(scores)
    )

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    rng.shuffle(indices)

    split_index = int(
        len(indices) *
        TEST_VALIDATION_RATIO
    )

    validation_indices = indices[
        :split_index
    ]

    holdout_indices = indices[
        split_index:
    ]

    return (
        scores[validation_indices],
        labels[validation_indices],
        [filenames[i] for i in validation_indices],

        scores[holdout_indices],
        labels[holdout_indices],
        [filenames[i] for i in holdout_indices],
    )


# ============================================================
# PROCESS ONE CATEGORY
# ============================================================

def evaluate_category(category):

    print()
    print("=" * 70)
    print(f"OPTIMIZING: {category.upper()}")
    print("=" * 70)

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = load_model(category)

    print("Model loaded successfully.")

    # --------------------------------------------------------
    # TRAINING GOOD
    # --------------------------------------------------------

    normal_errors = collect_training_good_errors(
        model,
        category
    )

    if len(normal_errors) == 0:

        raise RuntimeError(
            f"No training-good images found for {category}"
        )

    print(
        f"Training good images : {len(normal_errors)}"
    )

    print(
        f"Normal error min     : "
        f"{normal_errors.min():.8f}"
    )

    print(
        f"Normal error max     : "
        f"{normal_errors.max():.8f}"
    )

    print(
        f"Normal error mean    : "
        f"{normal_errors.mean():.8f}"
    )

    print(
        f"Normal error median  : "
        f"{np.median(normal_errors):.8f}"
    )

    # --------------------------------------------------------
    # TEST DATA
    # --------------------------------------------------------

    scores, labels, filenames = collect_test_scores(
        model,
        category
    )

    if len(scores) == 0:

        raise RuntimeError(
            f"No test images found for {category}"
        )

    (
        validation_scores,
        validation_labels,
        validation_files,

        holdout_scores,
        holdout_labels,
        holdout_files,

    ) = split_test_data(
        scores,
        labels,
        filenames
    )

    print(
        f"Calibration samples : "
        f"{len(scores)}"
    )

    print(
        f"Holdout samples    : "
        f"{len(holdout_scores)}"
    )

    # --------------------------------------------------------
    # FIND BEST THRESHOLD
    # --------------------------------------------------------

    best = find_best_threshold(
        normal_errors,
        scores,
        labels,
    )

    threshold = best["threshold"]

    print()
    print(
        f"Selected threshold  : "
        f"{threshold:.8f}"
    )

    print(
        f"Threshold source    : "
        f"{best['source']}"
    )

    print(
        f"Calibration recall   : "
        f"{best['metrics']['recall']:.4f}"
    )

    # --------------------------------------------------------
    # TRAINING GOOD FALSE POSITIVES
    # --------------------------------------------------------

    training_predictions = (
        normal_errors >= threshold
    )

    training_false_positives = int(
        np.sum(training_predictions)
    )

    print(
        f"Training good above threshold : "
        f"{training_false_positives}/"
        f"{len(normal_errors)}"
    )

    # --------------------------------------------------------
    # PERCENTILE INFORMATION
    # --------------------------------------------------------

    percentile_values = {}

    for percentile in NORMAL_PERCENTILES:

        value = percentile_threshold(
            normal_errors,
            percentile
        )

        percentile_values[
            f"p{percentile}"
        ] = float(value)

    # --------------------------------------------------------
    # FINAL HOLDOUT
    # --------------------------------------------------------

    holdout_metrics = evaluate_threshold(
        holdout_scores,
        holdout_labels,
        threshold
    )

    print()
    print(
        "FINAL HELD-OUT TEST RESULTS"
    )

    print("-" * 50)

    print(
        f"Accuracy  : "
        f"{holdout_metrics['accuracy']:.4f}"
    )

    print(
        f"Precision : "
        f"{holdout_metrics['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{holdout_metrics['recall']:.4f}"
    )

    print(
        f"F1 Score  : "
        f"{holdout_metrics['f1']:.4f}"
    )

    print("-" * 50)

    # --------------------------------------------------------
    # RETURN RESULTS
    # --------------------------------------------------------

    return {
        "threshold": float(threshold),

        "threshold_source": best["source"],

        "validation_f1":
            float(best["metrics"]["f1"]),

        "validation_accuracy":
            float(best["metrics"]["accuracy"]),

        "validation_precision":
            float(best["metrics"]["precision"]),

        "validation_recall":
            float(best["metrics"]["recall"]),

        "holdout_f1":
            float(holdout_metrics["f1"]),

        "holdout_accuracy":
            float(holdout_metrics["accuracy"]),

        "holdout_precision":
            float(holdout_metrics["precision"]),

        "holdout_recall":
            float(holdout_metrics["recall"]),

        "training_good_images":
            int(len(normal_errors)),

        "training_good_max_error":
            float(normal_errors.max()),

        "training_good_mean_error":
            float(normal_errors.mean()),

        "training_good_median_error":
            float(np.median(normal_errors)),

        "training_good_above_threshold":
            training_false_positives,

        "normal_error_percentiles":
            percentile_values,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("VISIONINSPECT AI")
    print("AUTOENCODER THRESHOLD OPTIMIZATION")
    print("=" * 70)

    print(
        f"Device: {DEVICE}"
    )

    print(
        f"Image size: {IMAGE_SIZE}"
    )

    all_results = {}

    successful = 0

    # --------------------------------------------------------
    # ALL 15 CATEGORIES
    # --------------------------------------------------------

    for category in CATEGORIES:

        try:

            result = evaluate_category(
                category
            )

            all_results[category] = result

            successful += 1

        except Exception as e:

            print()
            print(
                f"ERROR processing "
                f"{category}: {e}"
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 100)
    print("AUTOENCODER THRESHOLD RESULTS")
    print("=" * 100)

    print(
        f"{'Category':<15}"
        f"{'Threshold':<14}"
        f"{'Val F1':<10}"
        f"{'Holdout F1':<12}"
        f"{'Accuracy':<10}"
        f"{'FP Train':<10}"
    )

    print("-" * 100)

    for category in CATEGORIES:

        if category not in all_results:

            continue

        result = all_results[
            category
        ]

        print(
            f"{category:<15}"
            f"{result['threshold']:<14.8f}"
            f"{result['validation_f1']:<10.4f}"
            f"{result['holdout_f1']:<12.4f}"
            f"{result['holdout_accuracy']:<10.4f}"
            f"{result['training_good_above_threshold']:<10}"
        )

    print("=" * 100)

    # ========================================================
    # SAVE JSON
    # ========================================================

    os.makedirs(
        os.path.dirname(THRESHOLD_FILE),
        exist_ok=True
    )

    with open(
        THRESHOLD_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_results,
            f,
            indent=4
        )

    print()
    print("Saved to:")
    print(THRESHOLD_FILE)

    print()
    print(
        f"Completed: "
        f"{successful}/{len(CATEGORIES)}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()