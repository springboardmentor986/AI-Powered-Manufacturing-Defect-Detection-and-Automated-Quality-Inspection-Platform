from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FusionResult:
    decision: str                  # "NORMAL" or "DEFECTIVE"
    resolved_defect_status: str    # "normal" or specific defect string (e.g. "crack", "anomaly")
    predicted_defect_type: str     # "good" / "normal" or specific defect string
    quadrant: str                  # "A", "B", "C", "D"
    is_anomalous: bool             # boolean flag for downstream pipeline gating
    explanation: str               # human-readable rationale for the decision


class DecisionFusionLayer:
    """
    Validation-driven decision fusion layer for VisionInspect AI.

    Coordinates the predictions of:
      1. Hierarchical Defect Classifier (good vs specific defect classes)
      2. Layer3 Anomaly Detector (anomaly score vs category-calibrated operating boundary)

    Evaluates the 4 operational quadrants derived from validation data (812 samples):
      - Quadrant A (Classifier Good, Anomaly Normal):
          Validated 99.2% true good. Resolves to NORMAL.
      - Quadrant D (Classifier Defect, Anomaly Normal):
          Validated 96.3% false alarms by the classifier on normal physical components.
          Anomaly detector correctly gates the false positive. Resolves to NORMAL.
      - Quadrant C (Classifier Defect, Anomaly Defective):
          Validated 95.4% true defectives where both models corroborate. Resolves to DEFECTIVE.
      - Quadrant B (Classifier Good, Anomaly Defective):
          Validated 84.6% true defectives missed by the classifier but captured by anomaly detector.
          Resolves to DEFECTIVE.
    """

    def __init__(self, anomaly_thresholds: Optional[Dict[str, float]] = None):
        self.anomaly_thresholds = anomaly_thresholds or {}

    def update_thresholds(self, anomaly_thresholds: Dict[str, float]):
        self.anomaly_thresholds = anomaly_thresholds

    def evaluate(
        self,
        category: str,
        pred_defect: str,
        defect_confidence: float,
        anomaly_score: float,
        category_threshold: Optional[float] = None,
        manual_defect_type: Optional[str] = None,
    ) -> FusionResult:
        """
        Execute validation-driven decision fusion.
        """
        cat = category.strip().lower() if category else "unknown"
        threshold = category_threshold
        if threshold is None:
            threshold = self.anomaly_thresholds.get(cat, 1.20)

        # 1. Determine model stances
        clean_pred_defect = (pred_defect or "good").strip().lower()
        clf_is_defective = clean_pred_defect not in ["good", "normal", "none"]
        anom_is_defective = float(anomaly_score) >= float(threshold)

        # 2. Manual override handling (if user explicitly provided a non-normal defect type)
        has_manual_defect = bool(
            manual_defect_type
            and manual_defect_type.strip().lower() not in ["good", "normal", "none"]
        )

        # 3. Quadrant Evaluation
        if not clf_is_defective and not anom_is_defective:
            # Quadrant A: Both agree normal
            quadrant = "A"
            decision = "NORMAL"
            resolved_defect = "normal"
            pred_defect_type = "good"
            is_anomalous = False
            explanation = (
                f"Quadrant A: Classifier ({clean_pred_defect}) and Anomaly Detector "
                f"({anomaly_score:.4f} < {threshold:.4f}) both confirm normal specimen."
            )

        elif clf_is_defective and not anom_is_defective:
            # Quadrant D: Classifier flagged defect, but anomaly detector shows normal features
            if has_manual_defect:
                # Manual specification override
                quadrant = "D_manual"
                decision = "DEFECTIVE"
                resolved_defect = manual_defect_type.strip().lower()
                pred_defect_type = clean_pred_defect
                is_anomalous = True
                explanation = "Manual defect specification active; overriding normal anomaly score."
            else:
                quadrant = "D"
                decision = "NORMAL"
                resolved_defect = "normal"
                pred_defect_type = "good"
                is_anomalous = False
                explanation = (
                    f"Quadrant D: Classifier predicted '{clean_pred_defect}', but Anomaly Detector "
                    f"({anomaly_score:.4f} < {threshold:.4f}) confirms normal physical distribution. "
                    f"Validation shows 96.3% of Quadrant D are classifier false alarms; resolving to NORMAL."
                )

        elif clf_is_defective and anom_is_defective:
            # Quadrant C: Both agree defective
            quadrant = "C"
            decision = "DEFECTIVE"
            resolved_defect = (
                manual_defect_type.strip().lower()
                if has_manual_defect
                else clean_pred_defect
            )
            pred_defect_type = clean_pred_defect
            is_anomalous = True
            explanation = (
                f"Quadrant C: Corroborated defect. Classifier indicates '{clean_pred_defect}' and "
                f"Anomaly Detector confirms divergence ({anomaly_score:.4f} >= {threshold:.4f})."
            )

        else:
            # Quadrant B: Classifier predicted good, but Anomaly Detector detected significant divergence
            quadrant = "B"
            decision = "DEFECTIVE"
            resolved_defect = (
                manual_defect_type.strip().lower()
                if has_manual_defect
                else "unclassified_anomaly"
            )
            pred_defect_type = "unclassified_anomaly"
            is_anomalous = True
            explanation = (
                f"Quadrant B: Anomaly divergence detected ({anomaly_score:.4f} >= {threshold:.4f}) "
                f"despite classifier predicting 'good'. Validation confirms 84.6% are genuine defects."
            )

        return FusionResult(
            decision=decision,
            resolved_defect_status=resolved_defect,
            predicted_defect_type=pred_defect_type,
            quadrant=quadrant,
            is_anomalous=is_anomalous,
            explanation=explanation,
        )
