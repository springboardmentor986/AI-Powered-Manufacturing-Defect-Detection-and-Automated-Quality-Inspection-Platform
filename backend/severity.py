def calculate_severity(anomaly_score, quality_score, defect_type):
    """
    Calculate defect severity for the prototype.

    Higher anomaly and lower quality indicate higher severity.
    """

    # Convert anomaly score into a 0-100 severity component
    if anomaly_score < -0.20:
        anomaly_component = 100
    elif anomaly_score < -0.10:
        anomaly_component = 80
    elif anomaly_score < 0:
        anomaly_component = 60
    else:
        anomaly_component = 20

    # Lower quality means higher severity
    quality_component = 100 - quality_score

    # Defect type contribution
    defect_component = {
        "Broken Large": 100,
        "Broken Small": 70,
        "Contamination": 80,
        "No Defect": 0
    }.get(defect_type, 50)

    # Weighted severity score
    severity_score = (
        anomaly_component * 0.40
        + quality_component * 0.30
        + defect_component * 0.30
    )

    severity_score = round(
        min(100, max(0, severity_score)),
        2
    )

    # Severity level
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
        "severity_level": severity_level
    }


if __name__ == "__main__":

    print("=" * 55)
    print("VisionInspect AI - Severity Scoring")
    print("=" * 55)

    result = calculate_severity(
        anomaly_score=-0.1138,
        quality_score=70,
        defect_type="Broken Small"
    )

    print("\nTest Result:")
    print(f"Severity Score : {result['severity_score']}")
    print(f"Severity Level : {result['severity_level']}")

    print("=" * 55)
    print("Severity module ready.")
    print("=" * 55)