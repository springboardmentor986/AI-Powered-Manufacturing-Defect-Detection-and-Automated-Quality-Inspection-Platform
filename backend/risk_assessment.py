# ============================================================
# VisionInspect AI - Risk Assessment
# Milestone 3
# ============================================================

def calculate_risk(
    severity_score,
    severity_level,
    defect_type,
    confidence
):
    severity_score = float(severity_score)
    confidence = float(confidence)

    # Risk score combines severity and model confidence
    risk_score = (
        (severity_score * 0.70) +
        (confidence * 0.30)
    )

    if defect_type == "No Defect":
        risk_score = 0
        risk_level = "Low"

    elif risk_score >= 80:
        risk_level = "Critical"

    elif risk_score >= 60:
        risk_level = "High"

    elif risk_score >= 40:
        risk_level = "Medium"

    else:
        risk_level = "Low"

    if risk_level == "Critical":
        recommendation = "Immediate inspection and production hold required."

    elif risk_level == "High":
        recommendation = "Inspect defective product and review production process."

    elif risk_level == "Medium":
        recommendation = "Perform secondary inspection before approval."

    else:
        recommendation = "Product can proceed with normal quality monitoring."

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "recommendation": recommendation
    }