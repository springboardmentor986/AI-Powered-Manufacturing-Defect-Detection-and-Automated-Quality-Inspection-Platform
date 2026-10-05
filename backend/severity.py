# ============================================================
# VisionInspect AI - Severity Assessment
# Milestone 3
# ============================================================

def calculate_severity(
    anomaly_score,
    quality_score,
    defect_type,
    confidence
):

    anomaly_score = float(anomaly_score)
    confidence = float(confidence or 0)

    # --------------------------------------------------------
    # NO DEFECT
    # --------------------------------------------------------
    # A normal/good product should always have zero severity.
    if defect_type == "No Defect":

        return {
            "severity_score": 0,
            "severity_level": "Low",
            "size_score": 0,
            "location_score": 0,
            "defect_type_score": 0,
            "confidence_score": 0
        }

    # --------------------------------------------------------
    # SIZE SCORE
    # --------------------------------------------------------

    if anomaly_score < -0.20:
        size_score = 100

    elif anomaly_score < -0.10:
        size_score = 70

    elif anomaly_score < 0:
        size_score = 40

    else:
        size_score = 20

    # --------------------------------------------------------
    # LOCATION SCORE
    # --------------------------------------------------------
    # Current model does not localize the defect.
    # Neutral prototype value is used.
    location_score = 50

    # --------------------------------------------------------
    # DEFECT TYPE SCORE
    # --------------------------------------------------------

    if defect_type == "Broken Large":
        defect_type_score = 100

    elif defect_type == "Broken Small":
        defect_type_score = 70

    elif defect_type == "Contamination":
        defect_type_score = 80

    else:
        defect_type_score = 50

    # --------------------------------------------------------
    # CONFIDENCE SCORE
    # --------------------------------------------------------

    confidence_score = max(
        0,
        min(
            100,
            confidence
        )
    )

    # --------------------------------------------------------
    # OFFICIAL WEIGHTS
    # --------------------------------------------------------
    # Size       = 30%
    # Location   = 25%
    # Defect Type= 25%
    # Confidence = 20%

    severity_score = (
        (size_score * 0.30) +
        (location_score * 0.25) +
        (defect_type_score * 0.25) +
        (confidence_score * 0.20)
    )

    severity_score = round(
        max(
            0,
            min(
                100,
                severity_score
            )
        ),
        2
    )

    # --------------------------------------------------------
    # SEVERITY LEVEL
    # --------------------------------------------------------

    if severity_score >= 80:
        severity_level = "Critical"

    elif severity_score >= 60:
        severity_level = "High"

    elif severity_score >= 40:
        severity_level = "Medium"

    else:
        severity_level = "Low"

    return {
        "severity_score": severity_score,
        "severity_level": severity_level,
        "size_score": size_score,
        "location_score": location_score,
        "defect_type_score": defect_type_score,
        "confidence_score": round(
            confidence_score,
            2
        )
    }