def calculate_confidence(anomaly_score, threshold):
    if anomaly_score <= threshold:
        confidence = (
            anomaly_score / threshold
        ) * 50
    else:
        excess_ratio = (
            (anomaly_score - threshold)
            / threshold
        )

        confidence = 50 + (
            excess_ratio * 25
        )

    confidence = min(
        max(confidence, 0),
        100
    )

    return round(confidence, 2)