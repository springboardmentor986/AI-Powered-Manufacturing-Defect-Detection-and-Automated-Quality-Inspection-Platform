from pathlib import Path

import cv2
import torch
import torch.nn as nn

from PIL import Image
from torchvision import models, transforms
from ultralytics import YOLO

from .severity import (
    get_defect_type_score,
    calculate_severity,
    assess_quality,
)


# ============================================================
# 1. PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# 2. MODEL PATHS
# ============================================================

YOLO_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "best (2).pt"
)

RESNET_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "defect_classifier_resnet18_final.pth"
)


# ============================================================
# 3. DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)


# ============================================================
# 4. RESNET18 CLASS NAMES
# ============================================================

class_names = [
    "bent",
    "bent_lead",
    "bent_wire",
    "broken",
    "broken_large",
    "broken_small",
    "broken_teeth",
    "cable_swap",
    "color",
    "combined",
    "contamination",
    "crack",
    "cut",
    "cut_inner_insulation",
    "cut_lead",
    "cut_outer_insulation",
    "damaged_case",
    "defective",
    "fabric_border",
    "fabric_interior",
    "faulty_imprint",
    "flip",
    "fold",
    "glue",
    "glue_strip",
    "gray_stroke",
    "hole",
    "liquid",
    "manipulated_front",
    "metal_contamination",
    "misplaced",
    "missing_cable",
    "missing_wire",
    "oil",
    "pill_type",
    "poke",
    "poke_insulation",
    "print",
    "rough",
    "scratch",
    "scratch_head",
    "scratch_neck",
    "split_teeth",
    "squeeze",
    "squeezed_teeth",
    "thread",
    "thread_side",
    "thread_top",
]


# ============================================================
# 5. LOAD YOLO
# ============================================================

print()
print("Loading YOLO26n...")

yolo_model = YOLO(
    str(YOLO_MODEL_PATH)
)

print("YOLO26n loaded successfully!")


# ============================================================
# 6. CREATE RESNET18
# ============================================================

print()
print("Loading ResNet18...")

resnet_model = models.resnet18(
    weights=None
)

resnet_model.fc = nn.Linear(
    resnet_model.fc.in_features,
    48
)


# ============================================================
# 7. LOAD RESNET18 WEIGHTS
# ============================================================

checkpoint = torch.load(
    RESNET_MODEL_PATH,
    map_location=device
)

if (
    isinstance(checkpoint, dict)
    and "model_state_dict" in checkpoint
):

    resnet_model.load_state_dict(
        checkpoint["model_state_dict"]
    )

else:

    resnet_model.load_state_dict(
        checkpoint
    )


resnet_model = resnet_model.to(device)

resnet_model.eval()

print("ResNet18 loaded successfully!")


# ============================================================
# 8. RESNET PREPROCESSING
# ============================================================

resnet_transform = transforms.Compose([

    transforms.Resize((224, 224)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# 9. CLASSIFY DEFECT CROP
# ============================================================

def classify_crop(crop):

    
    # --------------------------------------------------------
    # OpenCV uses BGR.
    # ResNet expects RGB.
    # --------------------------------------------------------

    crop_rgb = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2RGB
    )

    # --------------------------------------------------------
    # Convert NumPy array to PIL image
    # --------------------------------------------------------

    image = Image.fromarray(
        crop_rgb
    )

    # --------------------------------------------------------
    # Apply ResNet preprocessing
    # --------------------------------------------------------

    image_tensor = resnet_transform(
        image
    )

    # --------------------------------------------------------
    # Add batch dimension
    # --------------------------------------------------------

    image_tensor = image_tensor.unsqueeze(0)

    # --------------------------------------------------------
    # Move to CPU/GPU
    # --------------------------------------------------------

    image_tensor = image_tensor.to(device)

    # --------------------------------------------------------
    # Run classification
    # --------------------------------------------------------

    with torch.no_grad():

        output = resnet_model(
            image_tensor
        )

        probabilities = torch.softmax(
            output,
            dim=1
        )

        confidence, predicted = torch.max(
            probabilities,
            dim=1
        )

    # --------------------------------------------------------
    # Get predicted class
    # --------------------------------------------------------

    predicted_class = class_names[
        predicted.item()
    ]

    # --------------------------------------------------------
    # Convert confidence to percentage
    # --------------------------------------------------------

    confidence_percentage = (
        confidence.item() * 100
    )

    return {
        "defect_type": predicted_class,
        "confidence": round(
            confidence_percentage,
            2
        )
    }


# ============================================================
# 10. SIZE SCORE
# ============================================================

def calculate_size_score(
    x1,
    y1,
    x2,
    y2,
    image_width,
    image_height
):

   

    bbox_width = x2 - x1

    bbox_height = y2 - y1

    bbox_area = (
        bbox_width *
        bbox_height
    )

    image_area = (
        image_width *
        image_height
    )

    if image_area == 0:
        return 0

    area_ratio = (
        bbox_area /
        image_area
    )

    size_score = area_ratio * 100

    size_score = min(
        100,
        max(0, size_score)
    )

    return round(
        size_score,
        2
    )


# ============================================================
# 11. LOCATION SCORE
# ============================================================

def calculate_location_score(
    x1,
    y1,
    x2,
    y2,
    image_width,
    image_height
):

    

    # --------------------------------------------------------
    # Defect center
    # --------------------------------------------------------

    defect_center_x = (
        x1 + x2
    ) / 2

    defect_center_y = (
        y1 + y2
    ) / 2

    # --------------------------------------------------------
    # Image center
    # --------------------------------------------------------

    image_center_x = (
        image_width / 2
    )

    image_center_y = (
        image_height / 2
    )

    # --------------------------------------------------------
    # Normalize distance
    # --------------------------------------------------------

    normalized_x = (
        (defect_center_x - image_center_x)
        / (image_width / 2)
    )

    normalized_y = (
        (defect_center_y - image_center_y)
        / (image_height / 2)
    )

    # --------------------------------------------------------
    # Euclidean distance
    # --------------------------------------------------------

    distance = (
        normalized_x ** 2 +
        normalized_y ** 2
    ) ** 0.5

    # Maximum possible distance
    # from center to corner
    max_distance = 2 ** 0.5

    # --------------------------------------------------------
    # Convert distance into score
    # --------------------------------------------------------

    location_score = (
        1 -
        (distance / max_distance)
    ) * 100

    location_score = min(
        100,
        max(
            0,
            location_score
        )
    )

    return round(
        location_score,
        2
    )


# ============================================================
# 12. RUN COMPLETE INSPECTION
# ============================================================

def inspect_image(
    image_path,
    yolo_confidence=0.25
):

    

    image_path = Path(
        image_path
    )

    # --------------------------------------------------------
    # Check image
    # --------------------------------------------------------

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found:\n{image_path}"
        )

    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise ValueError(
            f"Could not read image:\n{image_path}"
        )

    # --------------------------------------------------------
    # Image dimensions
    # --------------------------------------------------------

    height, width = image.shape[:2]

    # --------------------------------------------------------
    # YOLO detection
    # --------------------------------------------------------

    results = yolo_model.predict(
        source=str(image_path),
        conf=yolo_confidence,
        verbose=False
    )

    result = results[0]

    # --------------------------------------------------------
    # No detections
    # --------------------------------------------------------

    if (
        result.boxes is None
        or len(result.boxes) == 0
    ):

        return {
            "status": "PASS",
            "defects_detected": 0,
            "detections": []
        }

    # --------------------------------------------------------
    # Process every detection
    # --------------------------------------------------------

    detections = []

    for index, box in enumerate(
        result.boxes
    ):

        # ====================================================
        # YOLO BOUNDING BOX
        # ====================================================

        x1, y1, x2, y2 = (
            box.xyxy[0]
            .cpu()
            .numpy()
        )

        # ----------------------------------------------------
        # Convert coordinates to integers
        # ----------------------------------------------------

        x1 = max(
            0,
            int(x1)
        )

        y1 = max(
            0,
            int(y1)
        )

        x2 = min(
            width,
            int(x2)
        )

        y2 = min(
            height,
            int(y2)
        )

        # ====================================================
        # YOLO CONFIDENCE
        # ====================================================

        yolo_conf = (
            box.conf[0]
            .cpu()
            .item()
        )

        # ====================================================
        # CROP DEFECT
        # ====================================================

        crop = image[
            y1:y2,
            x1:x2
        ]

        # ----------------------------------------------------
        # Make sure crop is valid
        # ----------------------------------------------------

        if crop.size == 0:
            continue

        # ====================================================
        # RESNET CLASSIFICATION
        # ====================================================

        classification = classify_crop(
            crop
        )

        defect_type = classification[
            "defect_type"
        ]

        classification_confidence = (
            classification["confidence"]
        )

        # ====================================================
        # SIZE SCORE
        # ====================================================

        size_score = calculate_size_score(
            x1,
            y1,
            x2,
            y2,
            width,
            height
        )

        # ====================================================
        # LOCATION SCORE
        # ====================================================

        location_score = calculate_location_score(
            x1,
            y1,
            x2,
            y2,
            width,
            height
        )

        # ====================================================
        # DEFECT TYPE SCORE
        # ====================================================

        try:

            defect_type_score = (
                get_defect_type_score(
                    defect_type
                )
            )

        except ValueError:

            defect_type_score = None

        # ====================================================
        # SEVERITY CALCULATION
        # ====================================================

        if defect_type_score is not None:

            severity = calculate_severity(

                size=size_score,

                location=location_score,

                defect_type=defect_type_score,

                confidence=classification_confidence
            )

            # =================================================
            # QUALITY ASSESSMENT
            # =================================================

            quality = assess_quality(

                defect_type=defect_type,

                classification_confidence=(
                    classification_confidence
                ),

                severity_score=(
                    severity["severity_score"]
                ),

                severity_level=(
                    severity["severity_level"]
                ),

                recommended_action=(
                    severity["recommended_action"]
                )
            )

        else:

            # ------------------------------------------------
            # No severity rule for this defect type
            # ------------------------------------------------

            severity = {

                "severity_score": None,

                "severity_level": "UNKNOWN",

                "recommended_action": (
                    "MANUAL_REVIEW"
                )
            }

            quality = {

                "quality_status": (
                    "MANUAL_REVIEW"
                ),

                "manual_review": True
            }

        # ====================================================
        # STORE DETECTION
        # ====================================================

        detection = {

            # ------------------------------------------------
            # Detection number
            # ------------------------------------------------

            "detection_number": (
                index + 1
            ),

            # ------------------------------------------------
            # YOLO information
            # ------------------------------------------------

            "bounding_box": [
                x1,
                y1,
                x2,
                y2
            ],

            "yolo_confidence": round(
                yolo_conf * 100,
                2
            ),

            # ------------------------------------------------
            # ResNet information
            # ------------------------------------------------

            "defect_type": (
                defect_type
            ),

            "classification_confidence": (
                classification_confidence
            ),

            # ------------------------------------------------
            # Severity inputs
            # ------------------------------------------------

            "size_score": (
                size_score
            ),

            "location_score": (
                location_score
            ),

            "defect_type_score": (
                defect_type_score
            ),

            "confidence_score": (
                classification_confidence
            ),

            # ------------------------------------------------
            # Final severity
            # ------------------------------------------------

            "severity_score": (
                severity[
                    "severity_score"
                ]
            ),

            "severity_level": (
                severity[
                    "severity_level"
                ]
            ),

            "recommended_action": (
                severity[
                    "recommended_action"
                ]
            ),

            # ------------------------------------------------
            # Final quality decision
            # ------------------------------------------------

            "quality_status": (
                quality[
                    "quality_status"
                ]
            ),

            "manual_review": (
                quality[
                    "manual_review"
                ]
            )
        }

        # ----------------------------------------------------
        # Add detection to list
        # ----------------------------------------------------

        detections.append(
            detection
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    if not detections:

        return {
            "status": "PASS",
            "defects_detected": 0,
            "detections": []
        }

    # ========================================================
    # DETERMINE OVERALL QUALITY STATUS
    # ========================================================
    #
    # Priority:
    #
    # FAIL
    #   ↓
    # REWORK
    #   ↓
    # REVIEW
    #   ↓
    # PASS
    #
    # The most serious detection determines
    # the overall inspection result.
    # ========================================================

    quality_priority = {
        "PASS": 0,
        "REVIEW": 1,
        "MANUAL_REVIEW": 1,
        "REWORK": 2,
        "FAIL": 3,
    }

    overall_status = "PASS"

    highest_priority = 0

    for detection in detections:

        status = detection.get(
            "quality_status",
            "MANUAL_REVIEW"
        )

        priority = quality_priority.get(
            status,
            1
        )

        if priority > highest_priority:

            highest_priority = priority

            # ------------------------------------------------
            # Convert MANUAL_REVIEW into REVIEW for the
            # overall inspection status.
            # ------------------------------------------------

            if status == "MANUAL_REVIEW":

                overall_status = "REVIEW"

            else:

                overall_status = status

    # ========================================================
    # RETURN FINAL RESULT
    # ========================================================

    return {

        "status": overall_status,

        "defects_detected": len(
            detections
        ),

        "detections": detections
    }