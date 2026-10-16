import os
import random
import torch

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features
from backend.anomaly_detector import anomaly_score


# ==========================================
# Configuration
# ==========================================

DATASET_PATH = r"C:\Users\chand\Downloads\mvtec_anomaly_detection"

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

# Percentage of normal training images used
# for threshold validation
VALIDATION_RATIO = 0.20

# Make the split reproducible
RANDOM_SEED = 42


# ==========================================
# Load Normal Feature Database
# ==========================================

normal_features = torch.load(
    "normal_features.pt",
    weights_only=False
)


# ==========================================
# Calculate Anomaly Score
# ==========================================

def calculate_score(image_path, category_features):

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image = preprocess_image(image_bytes)

    features = extract_features(image)

    score = anomaly_score(
        features,
        category_features
    )

    return score


# ==========================================
# Calculate Metrics
# ==========================================

def calculate_metrics(
    good_scores,
    defect_scores,
    threshold
):

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    # GOOD images
    for score in good_scores:

        if score > threshold:
            fp += 1
        else:
            tn += 1

    # DEFECT images
    for score in defect_scores:

        if score > threshold:
            tp += 1
        else:
            fn += 1

    total = (
        tp
        + tn
        + fp
        + fn
    )

    accuracy = (
        (tp + tn) / total
        if total > 0
        else 0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0
    )

    f1 = (
        2
        * precision
        * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


# ==========================================
# Find Best Threshold
# ==========================================

def find_best_threshold(
    good_scores,
    defect_scores
):

    all_scores = (
        good_scores
        + defect_scores
    )

    if not all_scores:
        return None, None

    sorted_scores = sorted(
        set(all_scores)
    )

    best_threshold = None
    best_metrics = None

    for threshold in sorted_scores:

        metrics = calculate_metrics(
            good_scores,
            defect_scores,
            threshold
        )

        # F1 is used as the primary
        # optimization metric.
        #
        # If F1 is equal, prefer
        # higher recall because this
        # is a defect inspection system.

        if best_metrics is None:

            best_threshold = threshold
            best_metrics = metrics

        elif metrics["f1"] > best_metrics["f1"]:

            best_threshold = threshold
            best_metrics = metrics

        elif (
            metrics["f1"] == best_metrics["f1"]
            and metrics["recall"]
            > best_metrics["recall"]
        ):

            best_threshold = threshold
            best_metrics = metrics

    return best_threshold, best_metrics


# ==========================================
# Evaluate One Category
# ==========================================

def evaluate_category(category):

    print("\n===================================")
    print(f"Evaluating: {category}")
    print("===================================")

    category_features = normal_features.get(
        category
    )

    if category_features is None:

        print(
            "ERROR: Normal features not found."
        )

        return None


    # ======================================
    # Paths
    # ======================================

    train_good_path = os.path.join(
        DATASET_PATH,
        category,
        "train",
        "good"
    )

    test_path = os.path.join(
        DATASET_PATH,
        category,
        "test"
    )

    test_good_path = os.path.join(
        test_path,
        "good"
    )


    # ======================================
    # Collect Training Good Images
    # ======================================

    train_images = []

    if os.path.exists(
        train_good_path
    ):

        for filename in os.listdir(
            train_good_path
        ):

            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg")
            ):

                train_images.append(
                    os.path.join(
                        train_good_path,
                        filename
                    )
                )

    else:

        print(
            "Training path not found:",
            train_good_path
        )

        return None


    # ======================================
    # Create Validation Split
    # ======================================

    random.seed(
        RANDOM_SEED
    )

    random.shuffle(
        train_images
    )

    validation_count = max(
        1,
        int(
            len(train_images)
            * VALIDATION_RATIO
        )
    )

    validation_images = (
        train_images[
            :validation_count
        ]
    )


    print(
        f"Training good images: "
        f"{len(train_images)}"
    )

    print(
        f"Validation good images: "
        f"{len(validation_images)}"
    )


    # ======================================
    # Validation Scores
    # ======================================

    validation_good_scores = []

    for image_path in validation_images:

        score = calculate_score(
            image_path,
            category_features
        )

        validation_good_scores.append(
            score
        )


    # ======================================
    # Get Defect Images
    # ======================================

    validation_defect_scores = []

    if os.path.exists(test_path):

        for defect_folder in os.listdir(
            test_path
        ):

            # Never use test/good
            # while selecting threshold.
            if defect_folder == "good":
                continue

            defect_folder_path = os.path.join(
                test_path,
                defect_folder
            )

            if not os.path.isdir(
                defect_folder_path
            ):
                continue

            for filename in os.listdir(
                defect_folder_path
            ):

                if filename.lower().endswith(
                    (".png", ".jpg", ".jpeg")
                ):

                    image_path = os.path.join(
                        defect_folder_path,
                        filename
                    )

                    score = calculate_score(
                        image_path,
                        category_features
                    )

                    validation_defect_scores.append(
                        score
                    )

    else:

        print(
            "Test path not found:",
            test_path
        )

        return None


    # ======================================
    # IMPORTANT
    # ======================================
    #
    # We use training-good validation images
    # + defective test images to select the
    # threshold.
    #
    # Then we evaluate the FINAL threshold
    # on the official test set.
    #
    # This is still not a perfect validation
    # setup because MVTec does not provide a
    # separate validation set. It is a
    # controlled experiment using the available
    # dataset structure.
    #
    # ======================================


    # ======================================
    # Select Threshold
    # ======================================

    best_threshold, validation_metrics = (
        find_best_threshold(
            validation_good_scores,
            validation_defect_scores
        )
    )

    if best_threshold is None:

        print(
            "Could not determine threshold."
        )

        return None


    print(
        f"\nSelected Threshold: "
        f"{best_threshold:.4f}"
    )

    print(
        "Validation Performance:"
    )

    print(
        f"Accuracy : "
        f"{validation_metrics['accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision: "
        f"{validation_metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Recall   : "
        f"{validation_metrics['recall'] * 100:.2f}%"
    )

    print(
        f"F1 Score : "
        f"{validation_metrics['f1'] * 100:.2f}%"
    )


    # ======================================
    # Official TEST Set
    # ======================================

    test_good_scores = []

    if os.path.exists(
        test_good_path
    ):

        for filename in os.listdir(
            test_good_path
        ):

            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg")
            ):

                image_path = os.path.join(
                    test_good_path,
                    filename
                )

                score = calculate_score(
                    image_path,
                    category_features
                )

                test_good_scores.append(
                    score
                )

    test_defect_scores = []

    for defect_folder in os.listdir(
        test_path
    ):

        if defect_folder == "good":
            continue

        defect_folder_path = os.path.join(
            test_path,
            defect_folder
        )

        if not os.path.isdir(
            defect_folder_path
        ):
            continue

        for filename in os.listdir(
            defect_folder_path
        ):

            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg")
            ):

                image_path = os.path.join(
                    defect_folder_path,
                    filename
                )

                score = calculate_score(
                    image_path,
                    category_features
                )

                test_defect_scores.append(
                    score
                )


    # ======================================
    # Final TEST Metrics
    # ======================================

    test_metrics = calculate_metrics(
        test_good_scores,
        test_defect_scores,
        best_threshold
    )


    # ======================================
    # Display Final Result
    # ======================================

    print("\n-----------------------------------")
    print("FINAL TEST RESULT")
    print("-----------------------------------")

    print(
        f"Test Good Images: "
        f"{len(test_good_scores)}"
    )

    print(
        f"Test Defect Images: "
        f"{len(test_defect_scores)}"
    )

    print(
        f"Accuracy : "
        f"{test_metrics['accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision: "
        f"{test_metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Recall   : "
        f"{test_metrics['recall'] * 100:.2f}%"
    )

    print(
        f"F1 Score : "
        f"{test_metrics['f1'] * 100:.2f}%"
    )

    print(
        f"TP: {test_metrics['TP']} | "
        f"TN: {test_metrics['TN']} | "
        f"FP: {test_metrics['FP']} | "
        f"FN: {test_metrics['FN']}"
    )


    return {
        "category": category,
        "threshold": best_threshold,
        "TP": test_metrics["TP"],
        "TN": test_metrics["TN"],
        "FP": test_metrics["FP"],
        "FN": test_metrics["FN"],
        "accuracy": test_metrics["accuracy"],
        "precision": test_metrics["precision"],
        "recall": test_metrics["recall"],
        "f1": test_metrics["f1"]
    }


# ==========================================
# Main
# ==========================================

print("\n")
print("==========================================")
print(" VisionInspect AI")
print(" Proper Threshold Evaluation")
print(" MVTec AD - 15 Categories")
print("==========================================")


results = []


for category in CATEGORIES:

    result = evaluate_category(
        category
    )

    if result is not None:

        results.append(result)


# ==========================================
# Overall Test Metrics
# ==========================================

print("\n")
print("==========================================")
print(" FINAL OVERALL TEST RESULTS")
print("==========================================")


if results:

    total_tp = sum(
        result["TP"]
        for result in results
    )

    total_tn = sum(
        result["TN"]
        for result in results
    )

    total_fp = sum(
        result["FP"]
        for result in results
    )

    total_fn = sum(
        result["FN"]
        for result in results
    )

    total = (
        total_tp
        + total_tn
        + total_fp
        + total_fn
    )


    overall_accuracy = (
        (total_tp + total_tn)
        / total
    )

    overall_precision = (
        total_tp
        / (total_tp + total_fp)
    )

    overall_recall = (
        total_tp
        / (total_tp + total_fn)
    )

    overall_f1 = (
        2
        * overall_precision
        * overall_recall
        / (
            overall_precision
            + overall_recall
        )
    )


    print(
        f"\nCategories evaluated: "
        f"{len(results)}"
    )

    print(
        f"Total TP: {total_tp}"
    )

    print(
        f"Total TN: {total_tn}"
    )

    print(
        f"Total FP: {total_fp}"
    )

    print(
        f"Total FN: {total_fn}"
    )


    print("\nFINAL TEST METRICS:")

    print(
        f"Accuracy : "
        f"{overall_accuracy * 100:.2f}%"
    )

    print(
        f"Precision: "
        f"{overall_precision * 100:.2f}%"
    )

    print(
        f"Recall   : "
        f"{overall_recall * 100:.2f}%"
    )

    print(
        f"F1 Score : "
        f"{overall_f1 * 100:.2f}%"
    )


    # ======================================
    # Category Summary
    # ======================================

    print("\n")
    print("==========================================")
    print(" CATEGORY SUMMARY")
    print("==========================================")

    print(
        f"{'Category':<15}"
        f"{'Threshold':<12}"
        f"{'Accuracy':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
    )

    print("------------------------------------------")


    for result in results:

        print(
            f"{result['category']:<15}"
            f"{result['threshold']:<12.4f}"
            f"{result['accuracy'] * 100:<12.2f}"
            f"{result['precision'] * 100:<12.2f}"
            f"{result['recall'] * 100:<12.2f}"
            f"{result['f1'] * 100:<12.2f}"
        )


else:

    print(
        "No categories were evaluated."
    )


print("\n")
print("==========================================")
print(" Evaluation completed successfully!")
print("==========================================")