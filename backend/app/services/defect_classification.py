"""
VisionInspect AI - Milestone 3
Defect Classification Service
"""


# Known defect types from the MVTec AD categories
CATEGORY_DEFECT_TYPES = {
    "bottle": [
        "Broken Large",
        "Broken Small",
        "Contamination",
    ],
    "cable": [
        "Missing Wire",
        "Bent Wire",
        "Damaged Cable",
        "Cut",
        "Exposed Wire",
    ],
    "screw": [
        "Thread Defect",
        "Head Defect",
        "Scratch",
        "Deformation",
    ],
    "tile": [
        "Crack",
        "Gray Stroke",
        "Oil",
        "Rough",
    ],
    "toothbrush": [
        "Defective Bristles",
        "Contamination",
        "Broken Bristle",
    ],
    "wood": [
        "Crack",
        "Hole",
        "Liquid",
        "Scratch",
    ],
}


def classify_defect(
    category: str,
    is_defective: bool,
    anomaly_score: float,
) -> dict:
    """
    Classify an anomaly into a defect category.

    Important:
    The current Isolation Forest model detects anomalies but
    does not perform pixel-level defect classification.

    Therefore this function provides a baseline classification
    using the product category and anomaly strength.
    """

    category = category.lower().strip()

    if not is_defective:
        return {
            "category": category,
            "defect_type": "No Defect",
            "classification_confidence": 100.0,
            "classification_method": "Anomaly Detection",
        }

    defect_types = CATEGORY_DEFECT_TYPES.get(
        category,
        ["Unknown Defect"]
    )

    # Stronger negative anomaly scores indicate stronger anomalies.
    anomaly_strength = max(
        0.0,
        min(1.0, abs(float(anomaly_score)) * 10)
    )

    classification_confidence = round(
        50.0 + (anomaly_strength * 40.0),
        2
    )

    # Baseline selection.
    # Specific physical defect identification will be improved
    # when localization/segmentation is implemented.
    if len(defect_types) == 1:
        selected_defect = defect_types[0]
    else:
        index = int(
            abs(float(anomaly_score)) * 1000
        ) % len(defect_types)

        selected_defect = defect_types[index]

    return {
        "category": category,
        "defect_type": selected_defect,
        "classification_confidence": classification_confidence,
        "classification_method": "Baseline Category Classification",
    }


def get_defect_type_score(defect_type: str) -> float:
    """
    Assign a severity contribution score to the defect type.

    Higher values represent potentially more serious defect types.
    """

    defect_type_lower = defect_type.lower()

    if defect_type_lower == "no defect":
        return 0.0

    critical_keywords = [
        "cut",
        "exposed",
        "broken",
        "missing",
        "deformation",
        "hole",
    ]

    high_keywords = [
        "crack",
        "damaged",
        "thread",
    ]

    medium_keywords = [
        "scratch",
        "contamination",
        "oil",
        "rough",
        "stroke",
    ]

    for keyword in critical_keywords:
        if keyword in defect_type_lower:
            return 90.0

    for keyword in high_keywords:
        if keyword in defect_type_lower:
            return 75.0

    for keyword in medium_keywords:
        if keyword in defect_type_lower:
            return 60.0

    return 50.0