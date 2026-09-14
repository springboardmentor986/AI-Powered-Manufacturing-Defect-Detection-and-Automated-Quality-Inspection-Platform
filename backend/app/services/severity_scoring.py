"""
Milestone 3 - Severity and Risk Scoring

VisionInspect AI
Manufacturing Defect Detection & Quality Inspection System
"""

# Weights defined by the project specification.
DEFECT_SIZE_WEIGHT = 0.30
DEFECT_LOCATION_WEIGHT = 0.25
DEFECT_TYPE_WEIGHT = 0.25
CONFIDENCE_WEIGHT = 0.20


def clamp_score(value: float) -> float:
    """Keep a score between 0 and 100."""
    return max(0.0, min(100.0, float(value)))


def get_severity_level(score: float) -> str:
    """
    Convert the weighted severity score into a risk level.
    """

    score = clamp_score(score)

    if score >= 80:
        return "Critical"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Medium"
    else:
        return "Low"


def calculate_severity(
    defect_size_score: float,
    defect_location_score: float,
    defect_type_score: float,
    confidence_score: float,
) -> dict:
    """
    Calculate severity using the project-defined weighted model.

    Defect Size       = 30%
    Defect Location   = 25%
    Defect Type       = 25%
    Confidence        = 20%
    """

    size = clamp_score(defect_size_score)
    location = clamp_score(defect_location_score)
    defect_type = clamp_score(defect_type_score)
    confidence = clamp_score(confidence_score)

    weighted_score = (
        size * DEFECT_SIZE_WEIGHT
        + location * DEFECT_LOCATION_WEIGHT
        + defect_type * DEFECT_TYPE_WEIGHT
        + confidence * CONFIDENCE_WEIGHT
    )

    severity_score = round(
        clamp_score(weighted_score),
        2
    )

    severity_level = get_severity_level(
        severity_score
    )

    return {
        "defect_size_score": round(size, 2),
        "defect_location_score": round(location, 2),
        "defect_type_score": round(defect_type, 2),
        "confidence_score": round(confidence, 2),
        "severity_score": severity_score,
        "severity_level": severity_level,
    }


def classify_defect_type(
    category: str,
    is_defective: bool,
) -> str:
    """
    Basic classification layer.

    The current anomaly detector tells us whether an image
    is anomalous. It does not yet identify a specific physical
    defect subtype from the image.
    """

    if not is_defective:
        return "No Defect"

    category = category.lower().strip()

    return f"{category.title()} Defect"


def calculate_quality_decision(
    is_defective: bool,
    severity_score: float,
) -> dict:
    """
    Generate a quality-control decision.
    """

    severity_score = clamp_score(severity_score)

    if not is_defective:
        return {
            "is_passed": True,
            "decision": "PASS",
            "risk_level": "Low",
            "recommendation": "Product accepted for production."
        }

    if severity_score >= 80:
        return {
            "is_passed": False,
            "decision": "FAIL",
            "risk_level": "Critical",
            "recommendation": (
                "Stop production review and perform immediate "
                "quality inspection."
            )
        }

    if severity_score >= 60:
        return {
            "is_passed": False,
            "decision": "FAIL",
            "risk_level": "High",
            "recommendation": (
                "Quarantine the product and perform detailed "
                "quality inspection."
            )
        }

    if severity_score >= 40:
        return {
            "is_passed": False,
            "decision": "FAIL",
            "risk_level": "Medium",
            "recommendation": (
                "Perform secondary inspection before release."
            )
        }

    return {
        "is_passed": False,
        "decision": "FAIL",
        "risk_level": "Low",
        "recommendation": (
            "Review the detected anomaly before release."
        )
    }