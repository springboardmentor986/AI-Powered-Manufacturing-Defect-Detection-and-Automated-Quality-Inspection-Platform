import os
import cv2
import numpy as np
from ultralytics import YOLO


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
YOLO_RUNS_DIR = os.path.join(BASE_DIR, "yolo", "runs")

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


def find_model(category):

    retrained = {
    "screw",
    "toothbrush",
    "transistor",
    "carpet",
    "wood"
}

    if category in retrained:
        path = os.path.join(
            YOLO_RUNS_DIR,
            f"{category}_defect_retrained",
            "weights",
            "best.pt"
        )
    else:
        path = os.path.join(
            YOLO_RUNS_DIR,
            f"{category}_defect",
            "weights",
            "best.pt"
        )

    return path if os.path.exists(path) else None


def get_defect_images(category):

    test_dir = os.path.join(
        DATASET_DIR,
        category,
        "test"
    )

    images = []

    for defect_type in sorted(os.listdir(test_dir)):

        if defect_type == "good":
            continue

        defect_dir = os.path.join(
            test_dir,
            defect_type
        )

        if not os.path.isdir(defect_dir):
            continue

        for filename in sorted(os.listdir(defect_dir)):

            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp")
            ):
                images.append(
                    (
                        os.path.join(defect_dir, filename),
                        defect_type
                    )
                )

    return images


def get_ground_truth_mask(category, defect_type, filename):

    name = os.path.splitext(filename)[0]

    mask_dir = os.path.join(
        DATASET_DIR,
        category,
        "ground_truth",
        defect_type
    )

    mask_path = os.path.join(
        mask_dir,
        name + "_mask.png"
    )

    if os.path.exists(mask_path):
        return mask_path

    return None


def mask_to_box(mask):

    ys, xs = np.where(mask > 0)

    if len(xs) == 0:
        return None

    x1 = int(xs.min())
    y1 = int(ys.min())
    x2 = int(xs.max())
    y2 = int(ys.max())

    return [x1, y1, x2, y2]


def calculate_iou(box1, box2):

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])

    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_width = max(0, x2 - x1)
    intersection_height = max(0, y2 - y1)

    intersection = (
        intersection_width *
        intersection_height
    )

    area1 = (
        max(0, box1[2] - box1[0]) *
        max(0, box1[3] - box1[1])
    )

    area2 = (
        max(0, box2[2] - box2[0]) *
        max(0, box2[3] - box2[1])
    )

    union = area1 + area2 - intersection

    if union == 0:
        return 0.0

    return intersection / union


def analyze_category(category):

    print()
    print("=" * 70)
    print(category.upper())
    print("=" * 70)

    model_path = find_model(category)

    if model_path is None:
        print("YOLO model not found.")
        return None

    model = YOLO(model_path)

    images = get_defect_images(category)

    total = 0
    detected = 0
    missed = 0

    iou_values = []

    iou_50 = 0
    iou_75 = 0

    for image_path, defect_type in images:

        total += 1

        filename = os.path.basename(image_path)

        mask_path = get_ground_truth_mask(
            category,
            defect_type,
            filename
        )

        if mask_path is None:
            print(
                f"Ground truth mask missing: {category}/{defect_type}/{filename}"
            )
            continue

        mask = cv2.imread(
            mask_path,
            cv2.IMREAD_GRAYSCALE
        )

        if mask is None:
            continue

        gt_box = mask_to_box(mask)

        if gt_box is None:
            continue

        results = model.predict(
            source=image_path,
            conf=0.05,
            imgsz=800,
            iou=0.45,
            max_det=20,
            verbose=False
        )

        predicted_boxes = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes.xyxy.cpu().numpy():

                predicted_boxes.append(
                    box.tolist()
                )

        if len(predicted_boxes) == 0:

            missed += 1
            continue

        detected += 1

        best_iou = 0.0

        for pred_box in predicted_boxes:

            iou = calculate_iou(
                pred_box,
                gt_box
            )

            best_iou = max(
                best_iou,
                iou
            )

        iou_values.append(best_iou)

        if best_iou >= 0.50:
            iou_50 += 1

        if best_iou >= 0.75:
            iou_75 += 1

    valid = len(iou_values)

    detection_rate = (
        detected / total * 100
        if total > 0
        else 0
    )

    mean_iou = (
        np.mean(iou_values)
        if valid > 0
        else 0
    )

    iou50_rate = (
        iou_50 / total * 100
        if total > 0
        else 0
    )

    iou75_rate = (
        iou_75 / total * 100
        if total > 0
        else 0
    )

    print()
    print(f"Total defect images : {total}")
    print(f"Detected            : {detected}")
    print(f"Missed              : {missed}")
    print(f"Detection rate      : {detection_rate:.2f}%")
    print(f"Valid IoU samples   : {valid}")
    print(f"Mean IoU             : {mean_iou:.4f}")
    print(f"IoU >= 0.50          : {iou_50}")
    print(f"IoU >= 0.75          : {iou_75}")
    print(f"IoU@0.50 rate        : {iou50_rate:.2f}%")
    print(f"IoU@0.75 rate        : {iou75_rate:.2f}%")

    return {
        "total": total,
        "detected": detected,
        "missed": missed,
        "detection_rate": detection_rate,
        "mean_iou": mean_iou,
        "iou50_rate": iou50_rate,
        "iou75_rate": iou75_rate,
    }


def main():

    print("=" * 80)
    print("VISIONINSPECT AI")
    print("YOLO DEFECT LOCALIZATION / IoU ANALYSIS")
    print("=" * 80)

    results = {}

    for category in CATEGORIES:

        try:

            result = analyze_category(category)

            if result:
                results[category] = result

        except Exception as e:

            print(
                f"ERROR - {category}: {e}"
            )

    print()
    print("=" * 100)
    print("YOLO LOCALIZATION SUMMARY")
    print("=" * 100)

    print(
        f"{'Category':<15}"
        f"{'Detect %':<12}"
        f"{'Mean IoU':<12}"
        f"{'IoU50 %':<12}"
        f"{'IoU75 %':<12}"
    )

    print("-" * 100)

    for category, r in results.items():

        print(
            f"{category:<15}"
            f"{r['detection_rate']:<12.2f}"
            f"{r['mean_iou']:<12.4f}"
            f"{r['iou50_rate']:<12.2f}"
            f"{r['iou75_rate']:<12.2f}"
        )

    print("=" * 100)


if __name__ == "__main__":
    main()