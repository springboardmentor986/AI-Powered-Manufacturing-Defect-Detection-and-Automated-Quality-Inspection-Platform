# ==========================================
# VisionInspect AI - Quality Risk Assessment
# ==========================================

def assess_quality_risk(
    severity_score,
    severity_level
):

    if severity_level == "LOW":
        risk_level = "LOW"
        recommended_action = "ACCEPT / MONITOR"

    elif severity_level == "MEDIUM":
        risk_level = "MODERATE"
        recommended_action = "REVIEW"

    elif severity_level == "HIGH":
        risk_level = "HIGH"
        recommended_action = "INSPECT / HOLD"

    else:
        risk_level = "VERY HIGH"
        recommended_action = "REJECT"

    return {
        "severity_score": severity_score,
        "severity_level": severity_level,
        "risk_level": risk_level,
        "recommended_action": recommended_action
    }