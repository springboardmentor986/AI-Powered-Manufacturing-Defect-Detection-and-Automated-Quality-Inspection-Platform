
import torch


def anomaly_score(features, normal_features):
    normal_center = torch.mean(
        normal_features,
        dim=0
    )

    distance = torch.norm(
        features.reshape(-1) - normal_center.reshape(-1)
    )

    return float(distance.item())


def predict_anomaly(
    features,
    normal_features,
    threshold=1.0
):
    score = anomaly_score(
        features,
        normal_features
    )

    if score > threshold:
        result = "DEFECT"
        decision = "ABOVE_THRESHOLD"
    else:
        result = "GOOD"
        decision = "WITHIN_THRESHOLD"

    return {
        "result": result,
        "anomaly_score": round(score, 4),
        "threshold": float(threshold),
        "decision": decision
    }