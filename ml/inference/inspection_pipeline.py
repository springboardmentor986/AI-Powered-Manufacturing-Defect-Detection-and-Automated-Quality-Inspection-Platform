import json
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn

from PIL import Image
from torchvision import models, transforms
from ultralytics import YOLO

from inference.quality_assessment import (
    analyze_image_quality,
    assess_quality,
)
from preprocessing.preprocess import (
    preprocess_image as preprocess_training_image,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset"
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
YOLO_DIR = BASE_DIR / "yolo"

THRESHOLDS_FILE = (
    BASE_DIR / "inference" / "thresholds.json"
)

MODEL_SELECTION_FILE = (
    BASE_DIR / "classification" / "model_selection.json"
)

CLASSIFICATION_MODELS_DIR = (
    BASE_DIR / "classification" / "saved_models"
)

IMAGE_SIZE = 224

# The autoencoder has already confirmed the image is anomalous. Use a stricter
# localization cutoff so weak background predictions are not shown as defects.
YOLO_CONFIDENCE = 0.10

# These detectors have poor validation precision and need a higher acceptance
# floor than the other categories to prevent weak background predictions from
# being shown as defects.
CATEGORY_YOLO_CONFIDENCE = {
    "carpet": 0.25,
    "cable": 0.25,
    "capsule": 0.25,
    "grid": 0.25,
    "toothbrush": 0.35,
    "transistor": 0.35,
}

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# SUPPORTED CATEGORIES
# ============================================================

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
# AUTOENCODER ARCHITECTURE
# ============================================================

class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            nn.Conv2d(32, 64, 3, 2, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.Conv2d(64, 128, 3, 2, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            nn.Conv2d(128, 256, 3, 2, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True)
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(
                256, 128, 3, 2, 1,
                output_padding=1
            ),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(
                128, 64, 3, 2, 1,
                output_padding=1
            ),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(
                64, 32, 3, 2, 1,
                output_padding=1
            ),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            nn.ConvTranspose2d(
                32, 3, 3, 2, 1,
                output_padding=1
            ),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

# ============================================================
# LOAD THRESHOLDS
# ============================================================

def load_thresholds():

    if not THRESHOLDS_FILE.exists():

        raise FileNotFoundError(
            f"Threshold file not found:\n"
            f"{THRESHOLDS_FILE}"
        )

    with open(
        THRESHOLDS_FILE,
        "r"
    ) as file:

        thresholds = json.load(file)

    return thresholds


# ============================================================
# GET CATEGORY THRESHOLD
# ============================================================

def get_category_threshold(
    thresholds,
    category
):

    if category not in thresholds:

        raise ValueError(
            f"No threshold found for category: "
            f"{category}"
        )

    value = thresholds[category]

    if isinstance(
        value,
        (int, float)
    ):

        return float(value)

    if isinstance(
        value,
        dict
    ):

        if "threshold" in value:

            return float(
                value["threshold"]
            )

    raise ValueError(
        f"Invalid threshold format for category: "
        f"{category}"
    )


# ============================================================
# LOAD AUTOENCODER
# ============================================================

def load_autoencoder(category):

    model_path = (
        SAVED_MODELS_DIR
        / f"{category}_autoencoder.pth"
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"Autoencoder model not found:\n"
            f"{model_path}"
        )

    model = ConvAutoencoder()

    state_dict = torch.load(
        model_path,
        map_location=DEVICE
    )

    model.load_state_dict(
        state_dict
    )

    model.to(DEVICE)

    model.eval()

    return model


# ============================================================
# PREPROCESS IMAGE FOR AUTOENCODER
# ============================================================

def preprocess_image(image_path):
    normalized, _ = preprocess_training_image(image_path)

    if normalized.shape != (IMAGE_SIZE, IMAGE_SIZE, 3):
        raise ValueError(
            f"Unexpected preprocessed image shape: {normalized.shape}"
        )

    tensor = torch.from_numpy(
        np.transpose(normalized, (2, 0, 1))
    ).unsqueeze(0).to(DEVICE)

    return tensor


# ============================================================
# AUTOENCODER ANOMALY DETECTION
# ============================================================

def detect_anomaly(
    model,
    image_tensor,
    threshold
):

    with torch.no_grad():

        reconstructed = model(
            image_tensor
        )

        error = torch.mean(
            (
                image_tensor
                - reconstructed
            ) ** 2
        ).item()

    if error >= threshold:

        status = "DEFECT"

    else:

        status = "GOOD"

    return status, error


# ============================================================
# GET YOLO MODEL PATH
# ============================================================

def get_yolo_model_path(category):

    if category == "bottle":

        candidates = [
            YOLO_DIR / "runs" / "bottle_defect_improved" / "weights" / "best.pt",
            YOLO_DIR / "runs" / "bottle_defect" / "weights" / "best.pt",
            YOLO_DIR / "runs" / "bottle_defect_final" / "weights" / "best.pt",
        ]

    elif category in [
        "toothbrush",
        "transistor",
        "screw",
        "carpet",
        "wood"
    ]:

        candidates = [
            YOLO_DIR / "runs" / f"{category}_defect_final" / "weights" / "best.pt",
            YOLO_DIR / "runs" / f"{category}_defect_retrained" / "weights" / "best.pt",
            YOLO_DIR / "runs" / f"{category}_defect" / "weights" / "best.pt",
        ]

    else:

        candidates = [
            YOLO_DIR / "runs" / f"{category}_defect_final" / "weights" / "best.pt",
            YOLO_DIR / "runs" / f"{category}_defect" / "weights" / "best.pt",
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


# ============================================================
# YOLO DEFECT LOCALIZATION
# ============================================================
#
# Robust inference:
# 1. High-resolution YOLO inference
# 2. Augmented YOLO inference
# 3. Merge duplicate detections
#
# YOLO remains the primary localization model.
# ============================================================

def localize_defect(
    category,
    image_path
):

    model_path = get_yolo_model_path(
        category
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"YOLO model not found:\n"
            f"{model_path}"
        )

    model = YOLO(
        str(model_path)
    )

    source_image = cv2.imread(str(image_path))

    if source_image is None:
        raise ValueError(
            f"Unable to read image for YOLO localization:\n{image_path}"
        )

    image_height, image_width = source_image.shape[:2]
    image_area = float(image_width * image_height)
    category_confidence = CATEGORY_YOLO_CONFIDENCE.get(
        category,
        YOLO_CONFIDENCE,
    )

    gray = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)

    # Estimate the product from pixels that differ from the image-border
    # background. A fixed dark-pixel threshold fails on dark products placed
    # on white backgrounds (for example zipper images), causing the blank
    # margin to be treated as the product region.
    border_size = max(2, min(image_height, image_width) // 40)
    border_pixels = np.concatenate(
        [
            source_image[:border_size].reshape(-1, 3),
            source_image[-border_size:].reshape(-1, 3),
            source_image[:, :border_size].reshape(-1, 3),
            source_image[:, -border_size:].reshape(-1, 3),
        ],
        axis=0,
    ).astype(np.float32)
    border_color = np.median(border_pixels, axis=0)
    color_distance = np.linalg.norm(
        source_image.astype(np.float32) - border_color,
        axis=2,
    )
    foreground = np.where(color_distance >= 18.0, 255, 0).astype(np.uint8)
    kernel = np.ones((5, 5), np.uint8)
    foreground = cv2.morphologyEx(foreground, cv2.MORPH_OPEN, kernel)
    foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        foreground,
        connectivity=8,
    )

    product_bbox = None
    max_area = 0
    minimum_product_area = max(1000, int(image_area * 0.01))

    for label_idx in range(1, num_labels):
        x, y, w, h, area = stats[label_idx]
        if area < minimum_product_area:
            continue
        if area > max_area:
            max_area = area
            product_bbox = (x, y, x + w, y + h)

    # --------------------------------------------------------
    # PASS 1: High-resolution inference
    # --------------------------------------------------------
    results_high = model.predict(
        source=str(image_path),
        imgsz=1280,
        conf=YOLO_CONFIDENCE,
        iou=0.45,
        max_det=20,
        verbose=False
    )

    # --------------------------------------------------------
    # PASS 2: Augmented inference
    # --------------------------------------------------------
    results_aug = model.predict(
        source=str(image_path),
        imgsz=1280,
        conf=YOLO_CONFIDENCE,
        iou=0.45,
        max_det=20,
        augment=True,
        verbose=False
    )

    raw_detections = []

    for results in [results_high, results_aug]:

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                coordinates = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .tolist()
                )

                confidence = float(
                    box.conf[0]
                    .cpu()
                    .item()
                )

                if confidence < category_confidence:
                    continue

                x1, y1, x2, y2 = coordinates

                if x2 <= x1 or y2 <= y1:
                    continue

                box_area = (x2 - x1) * (y2 - y1)
                touches_border = (
                    x1 <= 1
                    or y1 <= 1
                    or x2 >= image_width - 1
                    or y2 >= image_height - 1
                )

                # Discard large border-touching boxes from the background. They
                # are usually false positives from dark margins or the image
                # frame, not actual product defects.
                if (
                    touches_border
                    and (
                        box_area / image_area >= 0.03
                        or category in {
                            "carpet",
                            "toothbrush",
                            "transistor",
                        }
                    )
                ):
                    continue

                # Carpet images can contain curtains, walls, and furniture at
                # the frame edges. Those regions are not the carpet surface.
                if category == "carpet":
                    box_center_x = (x1 + x2) / 2.0
                    box_center_y = (y1 + y2) / 2.0
                    if (
                        box_center_x < image_width * 0.25
                        or box_center_x > image_width * 0.80
                        or box_center_y < image_height * 0.30
                    ):
                        continue

                # The toothbrush dataset uses a centered product on a dark
                # background. Edge detections are background artifacts from
                # this low-precision detector, not valid defect locations.
                if category == "toothbrush":
                    box_center_x = (x1 + x2) / 2.0
                    if (
                        box_center_x < image_width * 0.25
                        or box_center_x > image_width * 0.75
                    ):
                        continue

                # Reject detections placed far outside the product region when a
                # dominant product blob has been found. A true defect should
                # overlap the product silhouette substantially, not sit in the
                # background or padded blank areas.
                if product_bbox is not None:
                    px0, py0, px1, py1 = product_bbox
                    product_area = max(1.0, (px1 - px0) * (py1 - py0))

                    inter_x1 = max(x1, px0)
                    inter_y1 = max(y1, py0)
                    inter_x2 = min(x2, px1)
                    inter_y2 = min(y2, py1)
                    inter_w = max(0.0, inter_x2 - inter_x1)
                    inter_h = max(0.0, inter_y2 - inter_y1)
                    overlap_area = inter_w * inter_h
                    overlap_ratio = overlap_area / max(box_area, 1.0)
                    box_center_x = (x1 + x2) / 2.0
                    box_center_y = (y1 + y2) / 2.0

                    if (
                        box_center_x < px0 or box_center_x > px1 or
                        box_center_y < py0 or box_center_y > py1
                    ):
                        continue

                    if overlap_ratio < 0.20:
                        continue

                    if box_area > 0.75 * product_area and overlap_area < 0.25 * product_area:
                        continue

                raw_detections.append({
                    "class": "defect",
                    "confidence": confidence,
                    "bbox": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    }
                })

    # --------------------------------------------------------
    # Remove duplicate boxes from the two inference passes
    # --------------------------------------------------------
    def box_iou(box_a, box_b):

        ax1, ay1 = box_a["x1"], box_a["y1"]
        ax2, ay2 = box_a["x2"], box_a["y2"]

        bx1, by1 = box_b["x1"], box_b["y1"]
        bx2, by2 = box_b["x2"], box_b["y2"]

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)

        intersection = inter_w * inter_h

        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

        union = area_a + area_b - intersection

        if union <= 0:
            return 0.0

        return intersection / union

    def box_overlap_ratio(box_a, box_b):
        ax1, ay1 = box_a["x1"], box_a["y1"]
        ax2, ay2 = box_a["x2"], box_a["y2"]
        bx1, by1 = box_b["x1"], box_b["y1"]
        bx2, by2 = box_b["x2"], box_b["y2"]

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        intersection = (
            max(0.0, inter_x2 - inter_x1)
            * max(0.0, inter_y2 - inter_y1)
        )

        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        smaller_area = min(area_a, area_b)

        if smaller_area <= 0:
            return 0.0

        return intersection / smaller_area

    raw_detections.sort(
        key=lambda d: d["confidence"],
        reverse=True
    )

    detections = []

    for candidate in raw_detections:

        duplicate = False

        for kept in detections:

            if (
                box_iou(candidate["bbox"], kept["bbox"]) >= 0.45
                or box_overlap_ratio(candidate["bbox"], kept["bbox"]) >= 0.70
            ):

                duplicate = True
                break

        if not duplicate:

            detections.append({
                "class": "defect",
                "confidence": round(
                    candidate["confidence"],
                    4
                ),
                "bbox": {
                    "x1": round(candidate["bbox"]["x1"], 2),
                    "y1": round(candidate["bbox"]["y1"], 2),
                    "x2": round(candidate["bbox"]["x2"], 2),
                    "y2": round(candidate["bbox"]["y2"], 2)
                }
            })

    return detections


# ============================================================
# LOAD MODEL SELECTION
# ============================================================

def load_model_selection():

    if not MODEL_SELECTION_FILE.exists():

        raise FileNotFoundError(
            f"Model selection file not found:\n"
            f"{MODEL_SELECTION_FILE}"
        )

    with open(
        MODEL_SELECTION_FILE,
        "r"
    ) as file:

        selection = json.load(file)

    return selection


# ============================================================
# CREATE RESNET18 CLASSIFIER
# ============================================================

def create_classifier(
    num_classes
):

    model = models.resnet18(
        weights=None
    )

    model.fc = nn.Sequential(

        nn.Dropout(0.3),

        nn.Linear(
            model.fc.in_features,
            num_classes
        )
    )

    return model


# ============================================================
# LOAD RESNET18 CLASSIFIER
# ============================================================

def load_classifier(category):

    model_selection = (
        load_model_selection()
    )

    if category not in model_selection:

        raise ValueError(
            f"No classifier selected for "
            f"category: {category}"
        )

    model_filename = (
        model_selection[category]
    )

    model_path = (
        CLASSIFICATION_MODELS_DIR
        / model_filename
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"Classifier model not found:\n"
            f"{model_path}"
        )

    checkpoint = torch.load(
        model_path,
        map_location=DEVICE
    )

    class_names = checkpoint.get(
        "class_names"
    )

    if not class_names:

        raise ValueError(
            f"class_names not found in classifier "
            f"checkpoint:\n{model_path}"
        )

    model = create_classifier(
        len(class_names)
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(DEVICE)

    model.eval()

    return (
        model,
        class_names,
        model_filename
    )


# ============================================================
# CLASSIFIER PREPROCESSING
# ============================================================

classifier_transform = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(

        mean=[
            0.485,
            0.456,
            0.406
        ],

        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# CLASSIFY DEFECT
#
# CHANGE 2:
# Classify the YOLO defect crop instead of the whole image.
# ============================================================

def classify_defect(
    category,
    image_path,
    bbox=None
):

    (
        model,
        class_names,
        model_filename
    ) = load_classifier(
        category
    )

    image = Image.open(
        image_path
    ).convert("RGB")

    # ========================================================
    # CROP DETECTED DEFECT
    # ========================================================

    if bbox is not None:

        x1 = max(
            0,
            int(bbox["x1"])
        )

        y1 = max(
            0,
            int(bbox["y1"])
        )

        x2 = min(
            image.width,
            int(bbox["x2"])
        )

        y2 = min(
            image.height,
            int(bbox["y2"])
        )

        if x2 > x1 and y2 > y1:

            image = image.crop(
                (
                    x1,
                    y1,
                    x2,
                    y2
                )
            )

    image_tensor = (
        classifier_transform(
            image
        )
        .unsqueeze(0)
        .to(DEVICE)
    )

    with torch.no_grad():

        outputs = model(
            image_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        confidence, predicted_index = (
            torch.max(
                probabilities,
                dim=1
            )
        )

    predicted_index = (
        predicted_index.item()
    )

    confidence = (
        confidence.item()
    )

    defect_type = class_names[
        predicted_index
    ]

    return {

        "defect_type":
            defect_type,

        "confidence":
            round(
                confidence,
                4
            ),

        "model":
            model_filename
    }


# ============================================================
# COMPLETE INSPECTION PIPELINE
# ============================================================

def inspect_image(
    image_path,
    category
):

    category = (
        category
        .lower()
        .strip()
    )

    if category not in CATEGORIES:

        raise ValueError(
            f"Invalid category: {category}\n"
            f"Available categories: {CATEGORIES}"
        )

    image_path = Path(
        image_path
    )

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found:\n"
            f"{image_path}"
        )

    print()
    print("=" * 70)
    print("VISIONINSPECT AI - INSPECTION")
    print("=" * 70)

    print(
        f"Category : {category}"
    )

    print(
        f"Image    : {image_path}"
    )

    print(
        f"Device   : {DEVICE}"
    )


    image_quality = analyze_image_quality(image_path)

    # ========================================================
    # STEP 1: LOAD THRESHOLD
    # ========================================================

    thresholds = load_thresholds()

    threshold = get_category_threshold(
        thresholds,
        category
    )


    # ========================================================
    # STEP 2: AUTOENCODER
    # ========================================================

    print()
    print("AUTOENCODER")
    print("-" * 70)

    print(
        f"Threshold : {threshold:.8f}"
    )

    autoencoder = load_autoencoder(
        category
    )


    # ========================================================
    # STEP 3: PREPROCESS
    # ========================================================

    image_tensor = preprocess_image(
        image_path
    )


    # ========================================================
    # STEP 4: ANOMALY DETECTION
    # ========================================================

    status, reconstruction_error = (
        detect_anomaly(
            autoencoder,
            image_tensor,
            threshold
        )
    )

    print(
        f"Error     : "
        f"{reconstruction_error:.8f}"
    )

    print(
        f"Decision  : {status}"
    )

    # ========================================================
    # AUTOENCODER GATES THE FLOW
    # ========================================================
    # If the autoencoder marks the image as GOOD, stop here and
    # do not run YOLO. If it marks the image as DEFECT, then
    # use YOLO only to localize the defect and classify it.
    # ========================================================
    if status == "GOOD":

        print()
        print("AUTOENCODER DECISION : GOOD")
        print("-" * 70)
        print("YOLO not run because the image passed the autoencoder screening.")
        print("FINAL DECISION : GOOD")

        return {
            "category": category,
            "status": "GOOD",
            "reconstruction_error": round(
                reconstruction_error,
                8
            ),
            "threshold": round(
                threshold,
                8
            ),
            "image_quality": image_quality,
            "classification": {
                "defect_type": "unknown",
                "confidence": 0,
                "model": None
            },
            "quality_assessment": {
                "severity": {
                    "score": 0,
                    "level": "Low",
                    "components": {
                        "size": 0,
                        "location": 0,
                        "defect_type": 0,
                        "confidence": 0
                    }
                },
                "quality_decision": "PASS",
                "recommendation":
                    "No defect detected. Product passes inspection."
            },
            "defects": []
        }

    # ========================================================
    # DEFECT → YOLO
    # ========================================================

    print()
    print("YOLO LOCALIZATION")
    print("-" * 70)

    detections = localize_defect(
        category,
        image_path
    )

    print(
        f"Detections : "
        f"{len(detections)}"
    )


    # ========================================================
    # NO YOLO DETECTION
    # ========================================================
    # Never turn an Autoencoder anomaly into GOOD merely
    # because YOLO could not localize it.
    # ========================================================
    if not detections and status == "DEFECT":

        print()
        print("NO DEFECT LOCATION FOUND")
        print("-" * 70)
        print(
            "Autoencoder detected an anomaly, "
            "but YOLO found no location."
        )
        print("FINAL DECISION : DEFECT")
        print("Recommendation  : Manual inspection required.")

        return {
            "category": category,
            "status": "DEFECT",
            "reconstruction_error": round(
                reconstruction_error,
                8
            ),
            "threshold": round(
                threshold,
                8
            ),
            "image_quality": image_quality,
            "classification": {
                "defect_type": "unknown",
                "confidence": 0,
                "model": None
            },
            "quality_assessment": {
                "severity": {
                    "score": 0,
                    "level": "Low",
                    "components": {
                        "size": 0,
                        "location": 0,
                        "defect_type": 0,
                        "confidence": 0
                    }
                },
                "quality_decision": "FAIL",
                "recommendation":
                    "Anomaly detected but no defect location was identified. "
                    "Manual inspection required."
            },
            "defects": []
        }

    # ========================================================
    # NO ANOMALY AND NO YOLO DETECTION → GOOD
    # ========================================================
    if not detections and status == "GOOD":

        print()
        print("NO DEFECT DETECTED")
        print("-" * 70)
        print("Autoencoder and YOLO found no defect.")
        print("FINAL DECISION : GOOD")

        return {
            "category": category,
            "status": "GOOD",
            "reconstruction_error": round(
                reconstruction_error,
                8
            ),
            "threshold": round(
                threshold,
                8
            ),
            "image_quality": image_quality,
            "classification": {
                "defect_type": "unknown",
                "confidence": 0,
                "model": None
            },
            "quality_assessment": {
                "severity": {
                    "score": 0,
                    "level": "Low",
                    "components": {
                        "size": 0,
                        "location": 0,
                        "defect_type": 0,
                        "confidence": 0
                    }
                },
                "quality_decision": "PASS",
                "recommendation":
                    "No defect detected. Product passes inspection."
            },
            "defects": []
        }


    for index, detection in enumerate(
        detections,
        start=1
    ):

        print()

        print(
            f"Defect {index}"
        )

        print(
            f"Confidence : "
            f"{detection['confidence']}"
        )

        print(
            f"BBox       : "
            f"{detection['bbox']}"
        )


    # ========================================================
    # DEFECT → RESNET18
    #
    # CHANGE 3:
    # Classify every YOLO detection separately.
    # ========================================================

    print()
    print("DEFECT CLASSIFICATION")
    print("-" * 70)

    for index, detection in enumerate(
        detections,
        start=1
    ):

        classification = classify_defect(
            category,
            image_path,
            detection["bbox"]
        )

        detection["defect_type"] = (
            classification["defect_type"]
        )

        detection[
            "classification_confidence"
        ] = (
            classification["confidence"]
        )

        detection[
            "classification_model"
        ] = (
            classification["model"]
        )

        print(
            f"Defect {index}: "
            f"{detection['defect_type']} "
            f"("
            f"{detection['classification_confidence']:.2%}"
            f")"
        )


    # ========================================================
    # QUALITY ASSESSMENT
    # ========================================================

    print()
    print("QUALITY ASSESSMENT")
    print("-" * 70)

    if detections:

        # Assess the most confident detection
        primary_detection = max(
            detections,
            key=lambda d: d["confidence"]
        )

        quality_result = assess_quality(
            image_path,
            primary_detection
        )

    else:

        quality_result = {

            "severity": {

                "score": 0,

                "level": "Low",

                "components": {

                    "size": 0,

                    "location": 0,

                    "defect_type": 0,

                    "confidence": 0
                }
            },

            "quality_decision":
                "FAIL",

            "recommendation":
                "Defect detected but no "
                "location was identified. "
                "Manual inspection required."
        }


    print(
        f"Severity Score : "
        f"{quality_result['severity']['score']}"
    )

    print(
        f"Severity Level : "
        f"{quality_result['severity']['level']}"
    )

    print(
        f"Quality Decision : "
        f"{quality_result['quality_decision']}"
    )

    print(
        f"Recommendation : "
        f"{quality_result['recommendation']}"
    )


    # ========================================================
    # PRIMARY CLASSIFICATION
    # ========================================================

    if detections:

        primary_detection = max(
            detections,
            key=lambda d: d["confidence"]
        )

        primary_defect_type = (
            primary_detection["defect_type"]
        )

        primary_classification_confidence = (
            primary_detection[
                "classification_confidence"
            ]
        )

        primary_classification_model = (
            primary_detection[
                "classification_model"
            ]
        )

    else:

        primary_defect_type = "unknown"

        primary_classification_confidence = 0

        primary_classification_model = None


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("FINAL RESULT")
    print("-" * 70)

    print(
        "Status       : DEFECT"
    )

    print(
        f"Defect count : "
        f"{len(detections)}"
    )

    print(
        f"Defect type  : "
        f"{primary_defect_type}"
    )

    print(
        f"Classification confidence : "
        f"{primary_classification_confidence}"
    )

    print(
        f"Severity      : "
        f"{quality_result['severity']['level']}"
    )

    print(
        f"Severity score: "
        f"{quality_result['severity']['score']}"
    )

    print(
        f"Decision      : "
        f"{quality_result['quality_decision']}"
    )


    return {

        "category":
            category,

        "status":
            "DEFECT",

        "reconstruction_error":
            round(
                reconstruction_error,
                8
            ),

        "threshold":
            round(
                threshold,
                8
            ),

        "image_quality":
            image_quality,

        "classification": {

            "defect_type":
                primary_defect_type,

            "confidence":
                primary_classification_confidence,

            "model":
                primary_classification_model
        },

        "quality_assessment":
            quality_result,

        "defects":
            detections
    }


# ============================================================
# TEST ENTRY POINT
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("ML INSPECTION PIPELINE TEST")
    print("=" * 70)

    print()
    print("Available categories:")

    for category in CATEGORIES:

        print(
            f" - {category}"
        )

    print()

    category = input(
        "Enter product category: "
    ).strip().lower()

    image_path = input(
        "Enter image path: "
    ).strip().strip('"')

    try:

        result = inspect_image(
            image_path,
            category
        )

        print()
        print("=" * 70)
        print("PIPELINE RESULT")
        print("=" * 70)

        print(
            json.dumps(
                result,
                indent=4
            )
        )

    except Exception as error:

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(error)