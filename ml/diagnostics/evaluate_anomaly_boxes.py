import cv2
import json
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
import sys

# ============================================================
# PATH SETUP
# ============================================================

ML_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_DIR))

from preprocessing.preprocess import preprocess_image


DATASET_DIR = ML_DIR / "dataset"
MODEL_DIR = ML_DIR / "saved_models"
THRESHOLD_FILE = ML_DIR / "inference" / "thresholds.json"

RESULT_DIR = ML_DIR / "diagnostics" / "box_evaluation"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

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

IMAGE_SIZE = (224, 224)

# IoU needed to consider localization correct
IOU_THRESHOLD = 0.50

# Ignore extremely tiny anomaly regions
MIN_AREA = 20

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("DEVICE:", device)


# ============================================================
# AUTOENCODER
# ============================================================

class ConvAutoencoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(
                256, 128, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.ConvTranspose2d(
                128, 64, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.ConvTranspose2d(
                64, 32, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.ConvTranspose2d(
                32, 3, 3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


# ============================================================
# LOAD MODEL
# ============================================================

def load_model(category):

    model_path = MODEL_DIR / f"{category}_autoencoder.pth"

    model = ConvAutoencoder().to(device)

    state = torch.load(
        model_path,
        map_location=device
    )

    model.load_state_dict(state)
    model.eval()

    return model


# ============================================================
# LOAD THRESHOLDS
# ============================================================

with open(THRESHOLD_FILE, "r") as f:
    thresholds = json.load(f)


# ============================================================
# MASK → BOUNDING BOX
# ============================================================

def mask_to_box(mask):

    ys, xs = np.where(mask > 0)

    if len(xs) == 0:
        return None

    x1 = int(xs.min())
    y1 = int(ys.min())
    x2 = int(xs.max())
    y2 = int(ys.max())

    return [x1, y1, x2, y2]


# ============================================================
# GET GROUND-TRUTH MASK
# ============================================================

def get_ground_truth_mask(category, defect_type, image_name):

    mask_dir = (
        DATASET_DIR
        / category
        / "ground_truth"
        / defect_type
    )

    stem = Path(image_name).stem

    candidates = [
        mask_dir / f"{stem}_mask.png",
        mask_dir / f"{stem}.png",
    ]

    for path in candidates:
        if path.exists():
            mask = cv2.imread(
                str(path),
                cv2.IMREAD_GRAYSCALE
            )

            if mask is not None:
                mask = cv2.resize(
                    mask,
                    IMAGE_SIZE,
                    interpolation=cv2.INTER_NEAREST
                )

                _, mask = cv2.threshold(
                    mask,
                    127,
                    255,
                    cv2.THRESH_BINARY
                )

                return mask

    return None


# ============================================================
# GET ANOMALY BOXES
# ============================================================

def get_anomaly_boxes(category, image_path, model):

    processed, _ = preprocess_image(image_path)

    tensor = torch.from_numpy(
        np.transpose(processed, (2, 0, 1))
    ).unsqueeze(0).float().to(device)

    with torch.no_grad():
        reconstruction = model(tensor)

    reconstruction = (
        reconstruction
        .squeeze(0)
        .cpu()
        .numpy()
    )

    reconstruction = np.transpose(
        reconstruction,
        (1, 2, 0)
    )

    # Pixel-level anomaly map
    diff = np.abs(
        processed - reconstruction
    )

    anomaly_map = np.mean(
        diff,
        axis=2
    )

    threshold = thresholds[category]["threshold"]

    binary = (
        anomaly_map > threshold
    ).astype(np.uint8) * 255

    # Clean small noise
    kernel = np.ones((5, 5), np.uint8)

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel
    )

    # Connected components
    num_labels, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            binary
        )
    )

    boxes = []

    for i in range(1, num_labels):

        area = stats[i, cv2.CC_STAT_AREA]

        if area < MIN_AREA:
            continue

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        boxes.append([
            int(x),
            int(y),
            int(x + w - 1),
            int(y + h - 1)
        ])

    return boxes, binary


# ============================================================
# IOU
# ============================================================

def calculate_iou(box_a, box_b):

    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    if ix2 < ix1 or iy2 < iy1:
        return 0.0

    intersection = (
        (ix2 - ix1 + 1)
        * (iy2 - iy1 + 1)
    )

    area_a = (
        (ax2 - ax1 + 1)
        * (ay2 - ay1 + 1)
    )

    area_b = (
        (bx2 - bx1 + 1)
        * (by2 - by1 + 1)
    )

    union = area_a + area_b - intersection

    if union <= 0:
        return 0.0

    return intersection / union


# ============================================================
# EVALUATE ONE IMAGE
# ============================================================

def evaluate_image(
    category,
    defect_type,
    image_path,
    model
):

    gt_mask = get_ground_truth_mask(
        category,
        defect_type,
        image_path.name
    )

    if gt_mask is None:
        return None

    gt_box = mask_to_box(gt_mask)

    if gt_box is None:
        return None

    predicted_boxes, anomaly_binary = (
        get_anomaly_boxes(
            category,
            image_path,
            model
        )
    )

    best_iou = 0.0
    best_box = None

    for pred_box in predicted_boxes:

        iou = calculate_iou(
            pred_box,
            gt_box
        )

        if iou > best_iou:
            best_iou = iou
            best_box = pred_box

    detected = best_iou >= IOU_THRESHOLD

    return {
        "category": category,
        "defect_type": defect_type,
        "image": image_path.name,
        "ground_truth_box": gt_box,
        "predicted_box": best_box,
        "iou": best_iou,
        "detected": detected,
        "num_predicted_boxes": len(predicted_boxes),
    }


# ============================================================
# DRAW VISUAL RESULT
# ============================================================

def save_visual(
    category,
    defect_type,
    image_path,
    result,
    gt_mask
):

    image = cv2.imread(str(image_path))

    if image is None:
        return

    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    # Ground truth = GREEN
    gx1, gy1, gx2, gy2 = result["ground_truth_box"]

    cv2.rectangle(
        image,
        (gx1, gy1),
        (gx2, gy2),
        (0, 255, 0),
        2
    )

    # Prediction = RED
    if result["predicted_box"] is not None:

        px1, py1, px2, py2 = (
            result["predicted_box"]
        )

        cv2.rectangle(
            image,
            (px1, py1),
            (px2, py2),
            (0, 0, 255),
            2
        )

    text = (
        f"IoU: {result['iou']:.3f}"
    )

    cv2.putText(
        image,
        text,
        (5, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    output_dir = (
        RESULT_DIR
        / category
        / defect_type
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_dir
        / image_path.name
    )

    cv2.imwrite(
        str(output_path),
        image
    )


# ============================================================
# MAIN
# ============================================================

all_results = []

print("\n==============================================")
print("ANOMALY BOX EVALUATION - ALL 15 CATEGORIES")
print("==============================================\n")

for category in CATEGORIES:

    print(f"\n--- {category.upper()} ---")

    model = load_model(category)

    test_dir = (
        DATASET_DIR
        / category
        / "test"
    )

    defect_folders = [
        p for p in test_dir.iterdir()
        if p.is_dir()
        and p.name != "good"
    ]

    category_results = []

    for defect_folder in defect_folders:

        images = sorted(
            list(defect_folder.glob("*.png")) +
            list(defect_folder.glob("*.jpg")) +
            list(defect_folder.glob("*.jpeg"))
        )

        for image_path in images:

            result = evaluate_image(
                category,
                defect_folder.name,
                image_path,
                model
            )

            if result is None:
                continue

            all_results.append(result)
            category_results.append(result)

            print(
                f"{defect_folder.name:20s} "
                f"{image_path.name:10s} "
                f"IoU={result['iou']:.3f} "
                f"{'DETECTED' if result['detected'] else 'MISSED'}"
            )

            gt_mask = get_ground_truth_mask(
                category,
                defect_folder.name,
                image_path.name
            )

            save_visual(
                category,
                defect_folder.name,
                image_path,
                result,
                gt_mask
            )

    # --------------------------------------------------------
    # CATEGORY SUMMARY
    # --------------------------------------------------------

    if category_results:

        ious = [
            r["iou"]
            for r in category_results
        ]

        detected_count = sum(
            r["detected"]
            for r in category_results
        )

        total = len(category_results)

        print(
            f"\n{category.upper()} SUMMARY"
        )

        print(
            f"Images       : {total}"
        )

        print(
            f"Mean IoU     : {np.mean(ious):.4f}"
        )

        print(
            f"IoU >= 0.50  : "
            f"{detected_count}/{total} "
            f"({detected_count / total * 100:.2f}%)"
        )


# ============================================================
# OVERALL SUMMARY
# ============================================================

print("\n\n==============================================")
print("OVERALL RESULTS")
print("==============================================")

for category in CATEGORIES:

    results = [
        r for r in all_results
        if r["category"] == category
    ]

    if not results:
        continue

    mean_iou = np.mean([
        r["iou"]
        for r in results
    ])

    detection_rate = (
        sum(r["detected"] for r in results)
        / len(results)
        * 100
    )

    print(
        f"{category:12s} | "
        f"Mean IoU={mean_iou:.4f} | "
        f"Localization={detection_rate:.2f}%"
    )


# ============================================================
# SAVE JSON
# ============================================================

json_path = (
    RESULT_DIR
    / "all_results.json"
)

with open(json_path, "w") as f:
    json.dump(
        all_results,
        f,
        indent=2
    )

print("\n==============================================")
print("COMPLETE")
print("==============================================")

print(
    f"\nResults saved to:\n{RESULT_DIR}"
)

print(
    f"\nJSON saved to:\n{json_path}"
)