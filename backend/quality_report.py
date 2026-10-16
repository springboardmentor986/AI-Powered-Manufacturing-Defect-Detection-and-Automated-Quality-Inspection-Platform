# ==========================================
# VisionInspect AI - Production Quality Report
# ==========================================

def generate_quality_report(
    inspection_id,
    category,
    prediction,
    defect_type,
    severity_report,
    risk_report,
    product_status
):

    # --------------------------------------
    # Determine overall quality status
    # --------------------------------------

    if prediction == "GOOD":
        quality_status = "PASSED"
    else:
        quality_status = "FAILED"


    # --------------------------------------
    # Create production quality report
    # --------------------------------------

    report = {
        "inspection_id": inspection_id,

        "product_category": category,

        "inspection_result": prediction,

        "defect_type": defect_type,

        "quality_status": quality_status,

        "severity": {
            "score": (
                severity_report["severity_score"]
                if severity_report
                else None
            ),

            "level": (
                severity_report["severity_level"]
                if severity_report
                else None
            )
        },

        "quality_risk": {
            "risk_level": (
                risk_report["risk_level"]
                if risk_report
                else "LOW"
            ),

            "recommended_action": (
                risk_report["recommended_action"]
                if risk_report
                else "ACCEPT / MONITOR"
            )
        },

        "product_status": product_status
    }

    return report