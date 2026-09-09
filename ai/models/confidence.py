from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


class DetectionConfidence:
    """Calculates detection confidence (0-100%) against operating threshold boundaries."""

    def __init__(self, scores_path: str, anomaly_thresholds_path: Optional[str] = None):
        self.boundaries = {}

        if anomaly_thresholds_path and Path(anomaly_thresholds_path).exists():
            thresh_df = pd.read_csv(anomaly_thresholds_path)
            for _, row in thresh_df.iterrows():
                category = str(row["category"]).strip().lower()
                op_thresh = float(row["anomaly_threshold"])
                def_bnd = float(row.get("defect_boundary", op_thresh * 1.25))
                if def_bnd <= op_thresh:
                    def_bnd = max(float(row.get("defect_min", op_thresh * 1.15)), op_thresh * 1.15)
                self.boundaries[category] = {
                    "normal_boundary": op_thresh,
                    "defect_boundary": def_bnd,
                }
            return

        scores_path = Path(scores_path)
        if not scores_path.exists():
            raise FileNotFoundError(f"Confidence scores file not found: {scores_path}")

        scores = pd.read_csv(scores_path)
        required_columns = {"category", "label", "score"}
        missing_columns = required_columns - set(scores.columns)
        if missing_columns:
            raise ValueError(f"Missing columns: {sorted(missing_columns)}")

        for category in sorted(scores["category"].unique()):
            category_scores = scores[scores["category"] == category]
            normal_scores = category_scores[category_scores["label"] == "normal"]["score"].to_numpy()
            defect_scores = category_scores[category_scores["label"] == "defective"]["score"].to_numpy()

            if len(normal_scores) == 0:
                raise ValueError(f"No normal scores for category: {category}")
            if len(defect_scores) == 0:
                raise ValueError(f"No defective scores for category: {category}")

            normal_boundary = np.percentile(normal_scores, 95)
            defect_boundary = np.percentile(defect_scores, 25)
            if defect_boundary <= normal_boundary:
                defect_boundary = normal_boundary * 1.2

            self.boundaries[category] = {
                "normal_boundary": normal_boundary,
                "defect_boundary": defect_boundary,
            }

    def calculate(self, category: str, anomaly_score: float) -> float:
        if category not in self.boundaries:
            raise ValueError(f"Unknown category: {category}")

        normal_boundary = self.boundaries[category]["normal_boundary"]
        defect_boundary = self.boundaries[category]["defect_boundary"]

        if anomaly_score <= normal_boundary:
            return 0.0
        if anomaly_score >= defect_boundary:
            return 100.0

        confidence = ((anomaly_score - normal_boundary) / (defect_boundary - normal_boundary)) * 100.0
        return float(np.clip(confidence, 0.0, 100.0))