# ==========================================
# VisionInspect AI - Severity Scoring
# ==========================================

def calculate_severity(
    defect_size_score,
    location_score,
    defect_type_score,
    confidence_score
):
    """
    Calculate overall defect severity.

    Weights:
    Defect Size       = 30%
    Defect Location   = 25%
    Defect Type       = 25%
    Confidence        = 20%
    """

    severity_score = (
        defect_size_score * 0.30
        + location_score * 0.25
        + defect_type_score * 0.25
        + confidence_score * 0.20
    )

    severity_score = round(
        severity_score,
        2
    )

    if severity_score < 40:
        severity_level = "LOW"

    elif severity_score < 60:
        severity_level = "MEDIUM"

    elif severity_score < 80:
        severity_level = "HIGH"

    else:
        severity_level = "CRITICAL"

    return {
        "severity_score": severity_score,
        "severity_level": severity_level
    }