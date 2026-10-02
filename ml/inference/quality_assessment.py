# ============================================================
# VISIONINSPECT AI - QUALITY ASSESSMENT
# ============================================================

# Severity weights from project specification:
# Size       = 30%
# Location   = 25%
# Defect Type= 25%
# Confidence = 20%


# ============================================================
# DEFECT TYPE SCORE
# ============================================================

import cv2
import numpy as np
def analyze_image_quality(image_path):
    """
    Analyze basic image quality before defect detection.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read image for quality analysis")

    height, width = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Brightness
    brightness = float(np.mean(gray))

    # Contrast
    contrast = float(np.std(gray))

    # Sharpness / Blur
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Noise estimation
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    noise = float(np.std(gray.astype(np.float32) - blurred.astype(np.float32)))

    # -----------------------------
    # Individual quality scores
    # -----------------------------

    # Brightness score
    if 80 <= brightness <= 180:
        brightness_score = 100
    elif 60 <= brightness < 80 or 180 < brightness <= 200:
        brightness_score = 80
    elif 40 <= brightness < 60 or 200 < brightness <= 220:
        brightness_score = 60
    else:
        brightness_score = 30

    # Contrast score
    if contrast >= 50:
        contrast_score = 100
    elif contrast >= 35:
        contrast_score = 80
    elif contrast >= 20:
        contrast_score = 60
    else:
        contrast_score = 30

    # Sharpness score
    if sharpness >= 500:
        sharpness_score = 100
    elif sharpness >= 200:
        sharpness_score = 80
    elif sharpness >= 100:
        sharpness_score = 60
    else:
        sharpness_score = 30

    # Noise score
    if noise <= 5:
        noise_score = 100
    elif noise <= 10:
        noise_score = 80
    elif noise <= 20:
        noise_score = 60
    else:
        noise_score = 30

    # -----------------------------
    # Overall image quality score
    # -----------------------------

    quality_score = (
        brightness_score * 0.25
        + contrast_score * 0.25
        + sharpness_score * 0.30
        + noise_score * 0.20
    )

    quality_score = round(quality_score, 2)

    if quality_score >= 80:
        quality_status = "GOOD"
    elif quality_score >= 60:
        quality_status = "ACCEPTABLE"
    else:
        quality_status = "POOR"

    return {
        "resolution": f"{width}x{height}",
        "width": width,
        "height": height,
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "sharpness": round(sharpness, 2),
        "noise": round(noise, 2),
        "brightness_score": brightness_score,
        "contrast_score": contrast_score,
        "sharpness_score": sharpness_score,
        "noise_score": noise_score,
        "quality_score": quality_score,
        "quality_status": quality_status
    }

def get_defect_type_score(defect_type):

    critical_defects = [
        "broken_large",
        "missing_cable",
        "missing_wire",
        "cut_inner_insulation",
        "cut_outer_insulation"
    ]

    high_defects = [
        "broken_small",
        "crack",
        "hole",
        "cut",
        "damaged_case",
        "bent_lead",
        "cut_lead",
        "split_teeth",
        "broken_teeth"
    ]

    medium_defects = [
        "scratch",
        "contamination",
        "color",
        "glue",
        "rough",
        "fold",
        "poke",
        "thread",
        "bent"
    ]

    if defect_type in critical_defects:
        return 100

    if defect_type in high_defects:
        return 80

    if defect_type in medium_defects:
        return 60

    return 50


# ============================================================
# SIZE SCORE
# ============================================================

def calculate_size_score(
    bbox,
    image_width,
    image_height
):

    if not bbox:
        return 0

    box_width = (
        bbox["x2"] - bbox["x1"]
    )

    box_height = (
        bbox["y2"] - bbox["y1"]
    )

    defect_area = (
        box_width * box_height
    )

    image_area = (
        image_width * image_height
    )

    if image_area <= 0:
        return 0

    area_ratio = (
        defect_area / image_area
    )

    if area_ratio >= 0.30:
        return 100

    elif area_ratio >= 0.20:
        return 80

    elif area_ratio >= 0.10:
        return 60

    elif area_ratio >= 0.05:
        return 40

    else:
        return 20


# ============================================================
# LOCATION SCORE
# ============================================================

def calculate_location_score(
    bbox,
    image_width,
    image_height
):

    if not bbox:
        return 0

    x1 = bbox["x1"]
    y1 = bbox["y1"]
    x2 = bbox["x2"]
    y2 = bbox["y2"]

    center_x = (
        x1 + x2
    ) / 2

    center_y = (
        y1 + y2
    ) / 2

    normalized_x = (
        center_x / image_width
    )

    normalized_y = (
        center_y / image_height
    )

    distance_from_center = (
        (
            (normalized_x - 0.5) ** 2
            +
            (normalized_y - 0.5) ** 2
        ) ** 0.5
    )

    if distance_from_center <= 0.15:
        return 100

    elif distance_from_center <= 0.30:
        return 80

    elif distance_from_center <= 0.45:
        return 60

    else:
        return 40


# ============================================================
# CONFIDENCE SCORE
# ============================================================

def calculate_confidence_score(
    yolo_confidence,
    classifier_confidence
):

    average_confidence = (
        yolo_confidence
        + classifier_confidence
    ) / 2

    return round(
        average_confidence * 100,
        2
    )


# ============================================================
# CALCULATE SEVERITY
# ============================================================

def calculate_severity(
    size_score,
    location_score,
    defect_type_score,
    confidence_score
):

    severity_score = (

        size_score * 0.30

        +

        location_score * 0.25

        +

        defect_type_score * 0.25

        +

        confidence_score * 0.20
    )

    severity_score = round(
        severity_score,
        2
    )

    if severity_score >= 80:
        severity_level = "Critical"

    elif severity_score >= 60:
        severity_level = "High"

    elif severity_score >= 40:
        severity_level = "Medium"

    else:
        severity_level = "Low"

    return (
        severity_score,
        severity_level
    )


# ============================================================
# PASS / FAIL
# ============================================================

def get_pass_fail():

    # Any confirmed defect means the product fails
    # quality inspection.
    return "FAIL"


# ============================================================
# RECOMMENDATION
# ============================================================

def get_recommendation(
    severity_level
):

    if severity_level == "Critical":

        return (
            "Immediately stop production and "
            "inspect the affected batch."
        )

    elif severity_level == "High":

        return (
            "Reject the product and perform "
            "quality inspection on the affected batch."
        )

    elif severity_level == "Medium":

        return (
            "Reject the product and review "
            "the production process."
        )

    else:

        return (
            "Minor defect detected. "
            "Reject the product and continue "
            "monitoring production."
        )


# ============================================================
# COMPLETE QUALITY ASSESSMENT
# ============================================================

def assess_quality(
    image_path,
    defect
):

    import cv2

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise ValueError(
            f"Unable to read image:\n"
            f"{image_path}"
        )

    image_height, image_width = (
        image.shape[:2]
    )

    bbox = defect["bbox"]

    yolo_confidence = float(
        defect["confidence"]
    )

    classifier_confidence = float(
        defect[
            "classification_confidence"
        ]
    )

    defect_type = defect[
        "defect_type"
    ]


    # --------------------------------------------------------
    # Individual scores
    # --------------------------------------------------------

    size_score = calculate_size_score(
        bbox,
        image_width,
        image_height
    )

    location_score = calculate_location_score(
        bbox,
        image_width,
        image_height
    )

    defect_type_score = get_defect_type_score(
        defect_type
    )

    confidence_score = calculate_confidence_score(
        yolo_confidence,
        classifier_confidence
    )


    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    severity_score, severity_level = (
        calculate_severity(
            size_score,
            location_score,
            defect_type_score,
            confidence_score
        )
    )


    # --------------------------------------------------------
    # Pass / Fail
    # --------------------------------------------------------

    decision = get_pass_fail()


    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    recommendation = get_recommendation(
        severity_level
    )


    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {

        "severity": {

            "score":
                severity_score,

            "level":
                severity_level,

            "components": {

                "size":
                    size_score,

                "location":
                    location_score,

                "defect_type":
                    defect_type_score,

                "confidence":
                    confidence_score
            }
        },

        "quality_decision":
            decision,

        "recommendation":
            recommendation
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Quality assessment module loaded successfully."
    )