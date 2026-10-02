import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "all_categories"
PREDICTION_DIR = BASE_DIR.parent / "runs" / "predictions"

OUTPUT_DIR = BASE_DIR / "comparison_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# SETTINGS
# ============================================================

IOU_THRESHOLD = 0.50
CONF_THRESHOLD = 0.10

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
# FUNCTIONS
# ============================================================

def calculate_iou(box1, box2):
    """
    Calculate IoU between two boxes.
    Boxes are [x1, y1, x2, y2].
    """

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_width = max(0, x2 - x1)
    intersection_height = max(0, y2 - y1)

    intersection = intersection_width * intersection_height

    area1 = max(0, box1[2] - box1[0]) * max(
        0, box1[3] - box1[1]
    )

    area2 = max(0, box2[2] - box2[0]) * max(
        0, box2[3] - box2[1]
    )

    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def load_ground_truth(label_path, image_width, image_height):
    """
    Read YOLO ground-truth labels and convert
    normalized coordinates to pixel coordinates.
    """

    boxes = []

    if not label_path.exists():
        return boxes

    with open(label_path, "r") as f:
        lines = f.readlines()

    for line in lines:

        parts = line.strip().split()

        if len(parts) < 5:
            continue

        _, cx, cy, w, h = map(float, parts[:5])

        cx *= image_width
        cy *= image_height
        w *= image_width
        h *= image_height

        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2

        boxes.append(
            [x1, y1, x2, y2]
        )

    return boxes


def match_boxes(gt_boxes, prediction_boxes):
    """
    Match predicted boxes with ground-truth boxes
    using IoU >= threshold.

    Each ground-truth box can match only one prediction.
    """

    matched_gt = set()
    matched_predictions = set()

    matches = []

    # Calculate all IoUs
    candidates = []

    for pred_index, pred_box in enumerate(prediction_boxes):

        for gt_index, gt_box in enumerate(gt_boxes):

            iou = calculate_iou(
                pred_box,
                gt_box
            )

            if iou >= IOU_THRESHOLD:

                candidates.append(
                    (
                        iou,
                        pred_index,
                        gt_index
                    )
                )

    # Highest IoU first
    candidates.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    for iou, pred_index, gt_index in candidates:

        if pred_index in matched_predictions:
            continue

        if gt_index in matched_gt:
            continue

        matched_predictions.add(pred_index)
        matched_gt.add(gt_index)

        matches.append(
            (
                pred_index,
                gt_index,
                iou
            )
        )

    true_positives = len(matches)

    false_positives = (
        len(prediction_boxes)
        - true_positives
    )

    false_negatives = (
        len(gt_boxes)
        - true_positives
    )

    return (
        true_positives,
        false_positives,
        false_negatives,
        matches
    )


# ============================================================
# MAIN
# ============================================================

print("=" * 80)
print("YOLO PREDICTION vs GROUND TRUTH COMPARISON")
print("=" * 80)

print(f"IoU threshold : {IOU_THRESHOLD}")
print(f"Confidence    : {CONF_THRESHOLD}")

all_results = []

grand_tp = 0
grand_fp = 0
grand_fn = 0

# ============================================================
# PROCESS EACH CATEGORY
# ============================================================

for category in CATEGORIES:

    print("\n" + "=" * 80)
    print(f"CATEGORY: {category}")
    print("=" * 80)

    category_dir = DATASET_DIR / category

    image_dir = category_dir / "images" / "test"
    label_dir = category_dir / "labels" / "test"

    model_path = (
        BASE_DIR
        / "runs"
        / f"{category}_defect"
        / "weights"
        / "best.pt"
    )

    # --------------------------------------------------------
    # Handle special retrained models
    # --------------------------------------------------------

    if category == "bottle":

        improved_model = (
            BASE_DIR
            / "runs"
            / "bottle_defect_improved"
            / "weights"
            / "best.pt"
        )

        if improved_model.exists():
            model_path = improved_model

    elif category in [
        "toothbrush",
        "transistor",
        "screw"
    ]:

        retrained_model = (
            BASE_DIR
            / "runs"
            / f"{category}_defect_retrained"
            / "weights"
            / "best.pt"
        )

        if retrained_model.exists():
            model_path = retrained_model

    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    if not model_path.exists():

        print(
            f"MODEL NOT FOUND: {model_path}"
        )

        continue

    print(
        f"Model: {model_path}"
    )

    model = YOLO(str(model_path))

    category_tp = 0
    category_fp = 0
    category_fn = 0

    category_images = 0

    # --------------------------------------------------------
    # Process test images
    # --------------------------------------------------------

    image_files = sorted(
        image_dir.glob("*.png")
    )

    for image_path in image_files:

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            continue

        height, width = image.shape[:2]

        # ----------------------------------------------------
        # Ground truth
        # ----------------------------------------------------

        label_path = (
            label_dir
            / f"{image_path.stem}.txt"
        )

        gt_boxes = load_ground_truth(
            label_path,
            width,
            height
        )

        # ----------------------------------------------------
        # YOLO prediction
        # ----------------------------------------------------

        results = model.predict(
            source=str(image_path),
            conf=CONF_THRESHOLD,
            imgsz=640,
            verbose=False
        )

        prediction_boxes = []

        if results:

            result = results[0]

            if result.boxes is not None:

                for box in result.boxes.xyxy.cpu().numpy():

                    x1, y1, x2, y2 = box

                    prediction_boxes.append(
                        [
                            float(x1),
                            float(y1),
                            float(x2),
                            float(y2)
                        ]
                    )

        # ----------------------------------------------------
        # Match
        # ----------------------------------------------------

        tp, fp, fn, matches = match_boxes(
            gt_boxes,
            prediction_boxes
        )

        category_tp += tp
        category_fp += fp
        category_fn += fn

        category_images += 1

        # ----------------------------------------------------
        # Print image-level result
        # ----------------------------------------------------

        print(
            f"{image_path.name:35s} "
            f"GT={len(gt_boxes):2d} "
            f"YOLO={len(prediction_boxes):2d} "
            f"TP={tp:2d} "
            f"FP={fp:2d} "
            f"FN={fn:2d}"
        )

        # ----------------------------------------------------
        # Save comparison visualization
        # ----------------------------------------------------

        comparison_image = image.copy()

        # Ground truth = RED
        for gt_box in gt_boxes:

            x1, y1, x2, y2 = map(
                int,
                gt_box
            )

            cv2.rectangle(
                comparison_image,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                2
            )

            cv2.putText(
                comparison_image,
                "GT",
                (x1, max(20, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

        # YOLO prediction = GREEN
        for pred_index, pred_box in enumerate(
            prediction_boxes
        ):

            x1, y1, x2, y2 = map(
                int,
                pred_box
            )

            cv2.rectangle(
                comparison_image,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                comparison_image,
                "YOLO",
                (x1, min(height - 5, y2 + 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        output_category_dir = (
            OUTPUT_DIR / category
        )

        output_category_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        cv2.imwrite(
            str(
                output_category_dir
                / image_path.name
            ),
            comparison_image
        )

        all_results.append(
            {
                "category": category,
                "image": image_path.name,
                "ground_truth": len(gt_boxes),
                "predictions": len(prediction_boxes),
                "TP": tp,
                "FP": fp,
                "FN": fn
            }
        )

    # ========================================================
    # CATEGORY METRICS
    # ========================================================

    precision = (
        category_tp
        / (category_tp + category_fp)
        if category_tp + category_fp > 0
        else 0
    )

    recall = (
        category_tp
        / (category_tp + category_fn)
        if category_tp + category_fn > 0
        else 0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall > 0
        else 0
    )

    print("\nCATEGORY RESULT")

    print(
        f"Images    : {category_images}"
    )

    print(
        f"TP        : {category_tp}"
    )

    print(
        f"FP        : {category_fp}"
    )

    print(
        f"FN        : {category_fn}"
    )

    print(
        f"Precision : {precision:.4f}"
    )

    print(
        f"Recall    : {recall:.4f}"
    )

    print(
        f"F1 Score  : {f1:.4f}"
    )

    grand_tp += category_tp
    grand_fp += category_fp
    grand_fn += category_fn


# ============================================================
# OVERALL RESULTS
# ============================================================

overall_precision = (
    grand_tp
    / (grand_tp + grand_fp)
    if grand_tp + grand_fp > 0
    else 0
)

overall_recall = (
    grand_tp
    / (grand_tp + grand_fn)
    if grand_tp + grand_fn > 0
    else 0
)

overall_f1 = (
    2 * overall_precision * overall_recall
    / (overall_precision + overall_recall)
    if overall_precision + overall_recall > 0
    else 0
)

# ============================================================
# SAVE CSV
# ============================================================

csv_path = (
    OUTPUT_DIR
    / "comparison_results.csv"
)

with open(csv_path, "w") as f:

    f.write(
        "category,image,ground_truth,"
        "predictions,TP,FP,FN\n"
    )

    for result in all_results:

        f.write(
            f"{result['category']},"
            f"{result['image']},"
            f"{result['ground_truth']},"
            f"{result['predictions']},"
            f"{result['TP']},"
            f"{result['FP']},"
            f"{result['FN']}\n"
        )

# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 80)
print("FINAL OVERALL RESULT")
print("=" * 80)

print(
    f"True Positives  : {grand_tp}"
)

print(
    f"False Positives : {grand_fp}"
)

print(
    f"False Negatives : {grand_fn}"
)

print(
    f"Precision       : {overall_precision:.4f}"
)

print(
    f"Recall          : {overall_recall:.4f}"
)

print(
    f"F1 Score        : {overall_f1:.4f}"
)

print("\nComparison images:")
print(OUTPUT_DIR)

print("\nCSV:")
print(csv_path)

print("=" * 80)
print("COMPARISON COMPLETE")
print("=" * 80)