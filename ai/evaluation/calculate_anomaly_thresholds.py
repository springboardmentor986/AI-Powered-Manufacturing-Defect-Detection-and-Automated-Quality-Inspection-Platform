from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCORES_FILE = PROJECT_ROOT / "ai" / "evaluation" / "confidence_scores.csv"
OUTPUT_FILE = PROJECT_ROOT / "ai" / "models" / "anomaly_thresholds.csv"


def calculate_anomaly_thresholds():
    """
    Calculate category-specific anomaly detection thresholds from validation data.

    For each category:
      - normal_boundary: 95th percentile of normal validation anomaly scores
      - defect_boundary: 25th percentile of defective validation anomaly scores
      - anomaly_threshold: logarithmic midpoint (geometric mean) between
        normal_boundary and defect_boundary:
            threshold = sqrt(normal_boundary * defect_boundary)

    This threshold represents the data-derived decision boundary separating
    the normal validation distribution from the defective validation distribution.
    """
    scores = pd.read_csv(SCORES_FILE)

    records = []

    for category in sorted(scores["category"].unique()):
        category_scores = scores[scores["category"] == category]

        normal_scores = category_scores[
            category_scores["label"] == "normal"
        ]["score"].to_numpy()

        defect_scores = category_scores[
            category_scores["label"] == "defective"
        ]["score"].to_numpy()

        normal_boundary = float(np.percentile(normal_scores, 95))
        defect_boundary = float(np.percentile(defect_scores, 25))

        normal_max = float(np.max(normal_scores))
        defect_min = float(np.min(defect_scores))

        # Geometric mean between normal and defect boundaries
        anomaly_threshold = float(np.sqrt(normal_boundary * defect_boundary))

        records.append(
            {
                "category": category,
                "normal_boundary": normal_boundary,
                "defect_boundary": defect_boundary,
                "normal_max": normal_max,
                "defect_min": defect_min,
                "anomaly_threshold": round(anomaly_threshold, 5),
            }
        )

    df = pd.DataFrame(records)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved anomaly thresholds to {OUTPUT_FILE}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    calculate_anomaly_thresholds()
