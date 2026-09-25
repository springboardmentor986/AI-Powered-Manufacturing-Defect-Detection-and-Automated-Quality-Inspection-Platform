DEFECT_TYPE_SEVERITY = {

    "bent": 60,
    "bent_lead": 65,
    "bent_wire": 65,

    "broken": 90,
    "broken_large": 95,
    "broken_small": 75,
    "broken_teeth": 85,

    "cable_swap": 80,
    "color": 40,
    "combined": 85,

    "contamination": 70,
    "crack": 85,
    "cut": 80,

    "cut_inner_insulation": 75,
    "cut_lead": 80,
    "cut_outer_insulation": 80,

    "damaged_case": 85,
    "defective": 85,

    "fabric_border": 60,
    "fabric_interior": 60,

    "faulty_imprint": 45,
    "flip": 55,
    "fold": 55,

    "glue": 50,
    "glue_strip": 50,

    "gray_stroke": 50,
    "hole": 80,

    "liquid": 70,
    "manipulated_front": 70,

    "metal_contamination": 80,
    "misplaced": 65,

    "missing_cable": 85,
    "missing_wire": 85,

    "oil": 70,
    "pill_type": 70,

    "poke": 70,
    "poke_insulation": 75,

    "print": 45,
    "rough": 50,

    "scratch": 70,
    "scratch_head": 70,
    "scratch_neck": 70,

    "split_teeth": 80,
    "squeeze": 60,
    "squeezed_teeth": 80,

    "thread": 60,
    "thread_side": 65,
    "thread_top": 65,
}


# ============================================================
# GET DEFECT TYPE SCORE
# ============================================================

def get_defect_type_score(defect_type: str) -> float:

    if defect_type not in DEFECT_TYPE_SEVERITY:

        raise ValueError(
            f"Unknown defect type: {defect_type}"
        )

    return float(
        DEFECT_TYPE_SEVERITY[defect_type]
    )




def calculate_severity(
    size: float,
    location: float,
    defect_type: float,
    confidence: float,
):

    severity_score = (
        (size * 0.30)
        + (location * 0.25)
        + (defect_type * 0.25)
        + (confidence * 0.20)
    )

    # --------------------------------------------------------
    # Severity level
    # --------------------------------------------------------

    if severity_score >= 80:

        severity_level = "Critical"
        recommended_action = "Reject"

    elif severity_score >= 60:

        severity_level = "High"
        recommended_action = "Rework"

    elif severity_score >= 40:

        severity_level = "Medium"
        recommended_action = "Review"

    else:

        severity_level = "Low"
        recommended_action = "Accept"

    return {
        "severity_score": round(
            severity_score,
            2
        ),

        "severity_level": severity_level,

        "recommended_action": (
            recommended_action
        ),
    }


# ============================================================
# CONFIDENCE CHECK
# ============================================================

def check_confidence(
    confidence: float
):

    manual_review = confidence < 70

    return {
        "confidence_score": round(
            confidence,
            2
        ),

        "manual_review": manual_review,
    }


# ============================================================
# QUALITY ASSESSMENT
# ============================================================

def assess_quality(
    defect_type: str,
    classification_confidence: float,
    severity_score: float,
    severity_level: str,
    recommended_action: str,
):

    # --------------------------------------------------------
    # Low confidence always requires manual review
    # --------------------------------------------------------

    if classification_confidence < 70:

        return {
            "defect_type": defect_type,

            "classification_confidence": round(
                classification_confidence,
                2
            ),

            "severity_score": round(
                severity_score,
                2
            ),

            "severity_level": severity_level,

            "recommended_action": (
                "MANUAL_REVIEW"
            ),

            "quality_status": (
                "MANUAL_REVIEW"
            ),

            "manual_review": True,
        }

    # --------------------------------------------------------
    # Quality decision based on severity
    # --------------------------------------------------------

    if recommended_action == "Reject":

        quality_status = "FAIL"

    elif recommended_action == "Rework":

        quality_status = "REWORK"

    elif recommended_action == "Review":

        quality_status = "REVIEW"

    else:

        quality_status = "PASS"

    return {
        "defect_type": defect_type,

        "classification_confidence": round(
            classification_confidence,
            2
        ),

        "severity_score": round(
            severity_score,
            2
        ),

        "severity_level": severity_level,

        "recommended_action": (
            recommended_action
        ),

        "quality_status": quality_status,

        "manual_review": False,
    }