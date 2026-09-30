"""
VisionInspect AI
Milestone 3 - Defect Classification Service

Note:
The current Isolation Forest model detects anomalies.
It does not directly perform visual defect-type classification.

Therefore, defect-type selection remains a baseline mapping
based on the detected product category and anomaly score.
The defect names below are the actual MVTec AD test defect
folder names available in the project dataset.
"""


# ============================================================
# ACTUAL MVTec AD DEFECT TYPES
# ============================================================

CATEGORY_DEFECT_TYPES = {

    "bottle": [
        "broken_large",
        "broken_small",
        "contamination",
    ],

    "cable": [
        "bent_wire",
        "cable_swap",
        "combined",
        "cut_inner_insulation",
        "cut_outer_insulation",
        "missing_cable",
        "missing_wire",
        "poke_insulation",
    ],

    "capsule": [
        "crack",
        "faulty_imprint",
        "poke",
        "scratch",
        "squeeze",
    ],

    "carpet": [
        "color",
        "cut",
        "hole",
        "metal_contamination",
        "thread",
    ],

    "grid": [
        "bent",
        "broken",
        "glue",
        "metal_contamination",
        "thread",
    ],

    "hazelnut": [
        "crack",
        "cut",
        "hole",
        "print",
    ],

    "leather": [
        "color",
        "cut",
        "fold",
        "glue",
        "poke",
    ],

    "metal_nut": [
        "bent",
        "color",
        "flip",
        "scratch",
    ],

    "pill": [
        "color",
        "combined",
        "contamination",
        "crack",
        "faulty_imprint",
        "pill_type",
        "scratch",
    ],

    "screw": [
        "manipulated_front",
        "scratch_head",
        "scratch_neck",
        "thread_side",
        "thread_top",
    ],

    "tile": [
        "crack",
        "glue_strip",
        "gray_stroke",
        "oil",
        "rough",
    ],

    "toothbrush": [
        "defective",
    ],

    "transistor": [
        "bent_lead",
        "cut_lead",
        "damaged_case",
        "misplaced",
    ],

    "wood": [
        "color",
        "combined",
        "hole",
        "liquid",
        "scratch",
    ],

    "zipper": [
        "broken_teeth",
        "combined",
        "fabric_border",
        "fabric_interior",
        "rough",
        "split_teeth",
        "squeezed_teeth",
    ],
}


# ============================================================
# DEFECT CLASSIFICATION
# ============================================================

def classify_defect(
    category: str,
    is_defective: bool,
    anomaly_score: float,
) -> dict:
    """
    Classify an anomaly into a baseline MVTec defect type.

    Important:
    Isolation Forest detects whether an image is anomalous.
    It does not directly identify the physical defect type.

    Therefore, this function performs baseline defect-type
    selection using the category's known MVTec defect types
    and anomaly strength.

    A future supervised classification/localization model
    can replace this baseline.
    """

    category = category.lower().strip()

    # --------------------------------------------------------
    # Normal image
    # --------------------------------------------------------

    if not is_defective:
        return {
            "category": category,
            "defect_type": "No Defect",
            "classification_confidence": 100.0,
            "classification_method": "Anomaly Detection",
        }

    # --------------------------------------------------------
    # Get category-specific defect types
    # --------------------------------------------------------

    defect_types = CATEGORY_DEFECT_TYPES.get(
        category,
        ["unknown_defect"],
    )

    # --------------------------------------------------------
    # Calculate anomaly strength
    # --------------------------------------------------------

    anomaly_strength = max(
        0.0,
        min(
            1.0,
            abs(float(anomaly_score)) * 10,
        ),
    )

    classification_confidence = round(
        50.0 + (anomaly_strength * 40.0),
        2,
    )

    # --------------------------------------------------------
    # Baseline defect selection
    # --------------------------------------------------------

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
        "classification_confidence": (
            classification_confidence
        ),
        "classification_method": (
            "Baseline Category Classification"
        ),
    }


# ============================================================
# DEFECT TYPE SEVERITY CONTRIBUTION
# ============================================================

def get_defect_type_score(
    defect_type: str,
) -> float:
    """
    Assign a severity contribution score to the defect type.

    Higher values represent potentially more serious
    defect categories.

    This is a rule-based contribution used by the
    project's severity-scoring system.
    """

    defect_type_lower = defect_type.lower()

    # --------------------------------------------------------
    # No defect
    # --------------------------------------------------------

    if defect_type_lower == "no defect":
        return 0.0

    # --------------------------------------------------------
    # Critical-level keywords
    # --------------------------------------------------------

    critical_keywords = [
        "cut",
        "missing",
        "broken",
        "damaged",
        "hole",
        "poke",
        "squeeze",
        "split",
        "squeezed",
    ]

    # --------------------------------------------------------
    # High-level keywords
    # --------------------------------------------------------

    high_keywords = [
        "crack",
        "thread",
        "deformation",
        "bent",
        "defective",
        "manipulated",
        "faulty",
        "cut",
    ]

    # --------------------------------------------------------
    # Medium-level keywords
    # --------------------------------------------------------

    medium_keywords = [
        "scratch",
        "contamination",
        "color",
        "glue",
        "rough",
        "stroke",
        "fold",
        "print",
        "imprint",
        "combined",
        "fabric",
        "oil",
        "flip",
        "poke",
    ]

    # --------------------------------------------------------
    # Score evaluation
    # --------------------------------------------------------

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