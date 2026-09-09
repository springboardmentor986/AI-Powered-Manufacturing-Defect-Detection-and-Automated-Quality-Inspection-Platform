import argparse
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

from ai.models.inspection_pipeline import InspectionPipeline


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MVTec_ROOT = PROJECT_ROOT / "mvtec_anomaly_detection"

AI_ROOT = PROJECT_ROOT / "ai"

NORMAL_FEATURES = AI_ROOT / "models" / "normal_features_layer3.pt"
CONFIDENCE_SCORES = AI_ROOT / "evaluation" / "confidence_scores.csv"
SIZE_BOUNDARIES = AI_ROOT / "models" / "size_score_boundaries.csv"
SEGMENTATION_MODEL = AI_ROOT / "models" / "defect_segmenter_unet.pt"
SEGMENTATION_THRESHOLD = AI_ROOT / "models" / "segmentation_threshold.txt"

ANOMALY_THRESHOLDS = AI_ROOT / "models" / "anomaly_thresholds.csv"
POSTPROCESSING_CONFIG = AI_ROOT / "models" / "segmentation_postprocessing.json"

CATEGORY_CLASSIFIER = AI_ROOT / "models" / "category_classifier_resnet18.pt"
CATEGORY_CLASSES = AI_ROOT / "models" / "category_classes.json"

DEFECT_CLASSIFIER = AI_ROOT / "models" / "defect_classifier_hierarchical.pt"
DEFECT_CLASSES = AI_ROOT / "models" / "defect_classes.json"

RESULTS_DIR = AI_ROOT / "evaluation" / "random_test_results"

DEFAULT_SAMPLE_SIZE = 100
DEFAULT_SEED = 42


# ============================================================
# Dataset discovery
# ============================================================

def collect_mvtec_test_images():
    """
    Collect all images from the official MVTec AD test set.

    Ground truth is inferred from the directory structure:

        category/test/good/*.png
        category/test/<defect_type>/*.png
    """

    records = []

    if not MVTec_ROOT.exists():
        raise FileNotFoundError(
            f"MVTec dataset not found at:\n{MVTec_ROOT}"
        )

    category_dirs = [
        path
        for path in MVTec_ROOT.iterdir()
        if path.is_dir()
    ]

    for category_dir in sorted(category_dirs):

        test_dir = category_dir / "test"

        if not test_dir.exists():
            continue

        category = category_dir.name

        for defect_dir in sorted(test_dir.iterdir()):

            if not defect_dir.is_dir():
                continue

            defect_type = defect_dir.name

            for image_path in sorted(defect_dir.glob("*.png")):

                is_normal = defect_type == "good"

                records.append(
                    {
                        "image_path": str(image_path),
                        "category": category,
                        "defect_type": (
                            "normal"
                            if is_normal
                            else defect_type
                        ),
                        "is_defective": not is_normal,
                    }
                )

    return records


# ============================================================
# Random sampling
# ============================================================

def create_random_sample(
    records,
    sample_size,
    seed,
):
    """
    Create a reproducible random sample.

    The sample is stratified into normal and defective images
    so that both groups are represented.
    """

    random.seed(seed)

    normal_records = [
        record
        for record in records
        if not record["is_defective"]
    ]

    defective_records = [
        record
        for record in records
        if record["is_defective"]
    ]

    if sample_size >= len(records):
        print(
            f"Requested {sample_size} images, "
            f"but only {len(records)} are available."
        )

        return records.copy()

    # Approximately 50/50 normal and defective.
    normal_count = sample_size // 2
    defective_count = sample_size - normal_count

    if normal_count > len(normal_records):
        normal_count = len(normal_records)

    if defective_count > len(defective_records):
        defective_count = len(defective_records)

    selected_normal = random.sample(
        normal_records,
        normal_count,
    )

    selected_defective = random.sample(
        defective_records,
        defective_count,
    )

    selected = selected_normal + selected_defective

    random.shuffle(selected)

    return selected


# ============================================================
# Pipeline creation
# ============================================================

def create_pipeline():

    print("\nInitializing VisionInspect AI pipeline...")

    pipeline = InspectionPipeline(
        normal_features_path=str(
            NORMAL_FEATURES
        ),

        confidence_scores_path=str(
            CONFIDENCE_SCORES
        ),

        size_boundaries_path=str(
            SIZE_BOUNDARIES
        ),

        segmentation_model_path=str(
            SEGMENTATION_MODEL
        ),

        segmentation_threshold_path=str(
            SEGMENTATION_THRESHOLD
        ),

        anomaly_thresholds_path=str(
            ANOMALY_THRESHOLDS
        ),

        postprocessing_config_path=str(
            POSTPROCESSING_CONFIG
        ),

        category_classifier_path=str(
            CATEGORY_CLASSIFIER
        ),

        category_classes_path=str(
            CATEGORY_CLASSES
        ),

        defect_classifier_path=str(
            DEFECT_CLASSIFIER
        ),

        defect_classes_path=str(
            DEFECT_CLASSES
        ),
    )

    print("Pipeline initialized successfully.\n")

    return pipeline


# ============================================================
# Single image inference
# ============================================================

def run_single_prediction(
    pipeline,
    record,
    index,
    total,
):
    image_path = record["image_path"]

    print(
        f"[{index}/{total}] "
        f"{record['category']}/"
        f"{record['defect_type']}/"
        f"{Path(image_path).name}"
    )

    try:

        # IMPORTANT:
        #
        # No category.
        # No defect type.
        #
        # The production pipeline must determine
        # these automatically.

        result = pipeline.predict(
            image_path=image_path,
            category=None,
            defect_type=None,
        )

        predicted_category = (
            result.get("predicted_category")
            or result.get("category")
        )

        predicted_defect = (
            result.get("predicted_defect_type")
            or result.get("defect_type")
        )

        inspection_decision = (
            result.get("inspection_decision")
        )

        predicted_is_defective = (
            inspection_decision == "DEFECTIVE"
        )

        actual_is_defective = record["is_defective"]

        category_correct = (
            predicted_category
            == record["category"]
        )

        binary_correct = (
            predicted_is_defective
            == actual_is_defective
        )

        subtype_correct = None

        if actual_is_defective:

            subtype_correct = (
                predicted_defect
                == record["defect_type"]
            )

        # ----------------------------------------------------
        # Normal invariant
        # ----------------------------------------------------

        normal_invariant_pass = True

        if not actual_is_defective:

            normal_invariant_pass = (
                predicted_is_defective is False
                and predicted_defect == "normal"
                and float(
                    result.get(
                        "predicted_area_percent",
                        0,
                    )
                ) == 0.0
                and float(
                    result.get(
                        "severity_score",
                        0,
                    )
                ) == 0.0
                and result.get(
                    "quality_decision"
                ) == "Accept"
            )

        # ----------------------------------------------------
        # Severity consistency
        # ----------------------------------------------------

        severity_score = float(
            result.get(
                "severity_score",
                0,
            )
        )

        severity_level = result.get(
            "severity_level"
        )

        quality_decision = result.get(
            "quality_decision"
        )

        severity_consistent = True

        if severity_score >= 80:
            expected_level = "Critical"

        elif severity_score >= 60:
            expected_level = "High"

        elif severity_score >= 40:
            expected_level = "Medium"

        else:
            expected_level = "Low"

        if severity_level != expected_level:
            severity_consistent = False

        # Production rule:
        #
        # Critical / High -> Reject
        # Medium / Low    -> Accept

        if severity_score >= 60:
            expected_decision = "Reject"
        else:
            expected_decision = "Accept"

        if quality_decision != expected_decision:
            severity_consistent = False

        return {
            "image_path": image_path,
            "actual_category": record["category"],
            "predicted_category": predicted_category,

            "actual_defect_type": record["defect_type"],
            "predicted_defect_type": predicted_defect,

            "actual_binary": (
                "DEFECTIVE"
                if actual_is_defective
                else "NORMAL"
            ),

            "predicted_binary": (
                "DEFECTIVE"
                if predicted_is_defective
                else "NORMAL"
            ),

            "category_correct": category_correct,
            "binary_correct": binary_correct,
            "subtype_correct": subtype_correct,

            "anomaly_score": result.get(
                "anomaly_score"
            ),

            "classification_confidence": result.get(
                "classification_confidence"
            ),

            "detection_confidence": result.get(
                "confidence_score"
            ),

            "predicted_area_percent": result.get(
                "predicted_area_percent"
            ),

            "size_score": result.get(
                "size_score"
            ),

            "location_score": result.get(
                "location_score"
            ),

            "defect_type_score": result.get(
                "defect_type_score"
            ),

            "severity_score": severity_score,

            "severity_level": severity_level,

            "quality_decision": quality_decision,

            "normal_invariant_pass": (
                normal_invariant_pass
            ),

            "severity_consistent": (
                severity_consistent
            ),

            "error": None,
        }

    except Exception as error:

        print(
            f"    ERROR: {error}"
        )

        return {
            "image_path": image_path,
            "actual_category": record["category"],
            "predicted_category": None,

            "actual_defect_type": record["defect_type"],
            "predicted_defect_type": None,

            "actual_binary": (
                "DEFECTIVE"
                if record["is_defective"]
                else "NORMAL"
            ),

            "predicted_binary": None,

            "category_correct": False,
            "binary_correct": False,
            "subtype_correct": (
                False
                if record["is_defective"]
                else None
            ),

            "anomaly_score": None,
            "classification_confidence": None,
            "detection_confidence": None,
            "predicted_area_percent": None,
            "size_score": None,
            "location_score": None,
            "defect_type_score": None,
            "severity_score": None,
            "severity_level": None,
            "quality_decision": None,

            "normal_invariant_pass": (
                False
                if not record["is_defective"]
                else True
            ),

            "severity_consistent": False,

            "error": str(error),
        }


# ============================================================
# Metric calculation
# ============================================================

def calculate_metrics(results):

    dataframe = pd.DataFrame(results)

    successful = dataframe[
        dataframe["error"].isna()
    ].copy()

    if len(successful) == 0:
        raise RuntimeError(
            "No successful predictions."
        )

    # --------------------------------------------------------
    # Category accuracy
    # --------------------------------------------------------

    category_accuracy = accuracy_score(
        successful["actual_category"],
        successful["predicted_category"],
    )

    # --------------------------------------------------------
    # Binary classification
    # --------------------------------------------------------

    actual_binary = (
        successful["actual_binary"]
        == "DEFECTIVE"
    )

    predicted_binary = (
        successful["predicted_binary"]
        == "DEFECTIVE"
    )

    binary_accuracy = accuracy_score(
        actual_binary,
        predicted_binary,
    )

    precision = precision_score(
        actual_binary,
        predicted_binary,
        zero_division=0,
    )

    recall = recall_score(
        actual_binary,
        predicted_binary,
        zero_division=0,
    )

    f1 = f1_score(
        actual_binary,
        predicted_binary,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        actual_binary,
        predicted_binary,
        labels=[False, True],
    ).ravel()

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Defect subtype accuracy
    # --------------------------------------------------------

    defective_results = successful[
        successful["actual_binary"]
        == "DEFECTIVE"
    ]

    if len(defective_results) > 0:

        subtype_accuracy = (
            defective_results["subtype_correct"]
            .astype(bool)
            .mean()
        )

    else:
        subtype_accuracy = 0.0

    # --------------------------------------------------------
    # Normal invariant
    # --------------------------------------------------------

    normal_results = successful[
        successful["actual_binary"]
        == "NORMAL"
    ]

    normal_invariant_pass_rate = (
        normal_results["normal_invariant_pass"]
        .astype(bool)
        .mean()
        if len(normal_results) > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Severity consistency
    # --------------------------------------------------------

    severity_consistency = (
        successful["severity_consistent"]
        .astype(bool)
        .mean()
    )

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    failed_predictions = dataframe[
        dataframe["error"].notna()
    ]

    metrics = {
        "sample_size": len(dataframe),
        "successful_predictions": len(successful),
        "failed_predictions": len(
            failed_predictions
        ),

        "normal_images": int(
            (successful["actual_binary"] == "NORMAL")
            .sum()
        ),

        "defective_images": int(
            (
                successful["actual_binary"]
                == "DEFECTIVE"
            ).sum()
        ),

        "category_accuracy": category_accuracy,

        "binary_accuracy": binary_accuracy,

        "specificity": specificity,

        "precision": precision,

        "recall": recall,

        "f1": f1,

        "exact_defect_subtype_accuracy": (
            subtype_accuracy
        ),

        "normal_invariant_pass_rate": (
            normal_invariant_pass_rate
        ),

        "severity_consistency": (
            severity_consistency
        ),

        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }

    return dataframe, metrics


# ============================================================
# Display results
# ============================================================

def print_report(metrics):

    print("VisionInspect AI - Random MVTec Evaluation Report")

    print(
        f"\nSamples tested       : "
        f"{metrics['sample_size']}"
    )

    print(
        f"Successful           : "
        f"{metrics['successful_predictions']}"
    )

    print(
        f"Failed inference     : "
        f"{metrics['failed_predictions']}"
    )

    print(
        f"Normal images        : "
        f"{metrics['normal_images']}"
    )

    print(
        f"Defective images     : "
        f"{metrics['defective_images']}"
    )

    print("\n--- Classification ---")

    print(
        f"Category Accuracy    : "
        f"{metrics['category_accuracy'] * 100:.2f}%"
    )

    print(
        f"Normal/Defect Acc.   : "
        f"{metrics['binary_accuracy'] * 100:.2f}%"
    )

    print(
        f"Specificity          : "
        f"{metrics['specificity'] * 100:.2f}%"
    )

    print(
        f"Precision            : "
        f"{metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Recall               : "
        f"{metrics['recall'] * 100:.2f}%"
    )

    print(
        f"F1 Score             : "
        f"{metrics['f1'] * 100:.2f}%"
    )

    print(
        f"Exact Defect Type    : "
        f"{metrics['exact_defect_subtype_accuracy'] * 100:.2f}%"
    )

    print("\n--- System Invariants ---")

    print(
        f"Normal Invariant     : "
        f"{metrics['normal_invariant_pass_rate'] * 100:.2f}%"
    )

    print(
        f"Severity Consistency : "
        f"{metrics['severity_consistency'] * 100:.2f}%"
    )

    print("\n--- Confusion Matrix ---")

    print(
        f"True Negative        : "
        f"{metrics['true_negative']}"
    )

    print(
        f"False Positive       : "
        f"{metrics['false_positive']}"
    )

    print(
        f"False Negative       : "
        f"{metrics['false_negative']}"
    )

    print(
        f"True Positive        : "
        f"{metrics['true_positive']}"
    )



# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run random unseen MVTec evaluation "
            "through the VisionInspect AI production pipeline."
        )
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of random images to test.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility.",
    )

    args = parser.parse_args()

    print("VisionInspect AI: Random Unseen MVTec Evaluation")

    print("\nCollecting MVTec test images...")

    all_records = collect_mvtec_test_images()

    print(
        f"Total MVTec test images available: "
        f"{len(all_records)}"
    )

    sample_records = create_random_sample(
        all_records,
        sample_size=args.samples,
        seed=args.seed,
    )

    normal_count = sum(
        not record["is_defective"]
        for record in sample_records
    )

    defective_count = sum(
        record["is_defective"]
        for record in sample_records
    )

    print(
        f"\nRandom sample: {len(sample_records)} images"
    )

    print(
        f"Normal: {normal_count}"
    )

    print(
        f"Defective: {defective_count}"
    )

    print(
        f"Random seed: {args.seed}"
    )

    # --------------------------------------------------------
    # Initialize production pipeline
    # --------------------------------------------------------

    pipeline = create_pipeline()

    # --------------------------------------------------------
    # Run inference
    # --------------------------------------------------------

    print(
        "\nStarting automatic inference..."
    )

    print(
        "Ground-truth category and defect type "
        "are NOT supplied to the pipeline."
    )

    results = []

    total = len(sample_records)

    for index, record in enumerate(
        sample_records,
        start=1,
    ):

        result = run_single_prediction(
            pipeline=pipeline,
            record=record,
            index=index,
            total=total,
        )

        results.append(result)

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    dataframe, metrics = calculate_metrics(
        results
    )

    # --------------------------------------------------------
    # Save detailed results
    # --------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_csv = (
        RESULTS_DIR
        / f"random_mvtec_test_{len(sample_records)}_seed_{args.seed}.csv"
    )

    dataframe.to_csv(
        output_csv,
        index=False,
    )

    # --------------------------------------------------------
    # Display report
    # --------------------------------------------------------

    print_report(metrics)

    print(
        f"\nDetailed results saved to:\n"
        f"{output_csv}"
    )

    print(
        "\nEvaluation complete."
    )


if __name__ == "__main__":
    main()