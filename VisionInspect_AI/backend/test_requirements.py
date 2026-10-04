import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import anomaly_detector
from anomaly_detector import calculate_severity, classify_defect
import defect_model
from main import is_ground_truth_mask


class RequirementTests(unittest.TestCase):
    def test_severity_calculation_matches_requirements(self):
        result = calculate_severity(
            size_score=85,
            location_score=90,
            defect_type_score=95,
            confidence_score=92,
        )

        self.assertAlmostEqual(result["severity_score"], 88.0, places=1)
        self.assertEqual(result["severity_level"], "Critical")
        self.assertIn("Reject Product", result["recommended_action"])

    def test_moderate_single_defect_is_not_misclassified_as_large(self):
        image_area = 100 * 100
        defect_type = classify_defect(
            defect_count=1,
            total_defect_area=1000,
            bounding_boxes=[(10, 10, 30, 30)],
            image_area=image_area,
        )

        self.assertEqual(defect_type, "broken_small")

    def test_ground_truth_mask_filename_is_identified(self):
        self.assertTrue(is_ground_truth_mask("016_mask.png"))
        self.assertTrue(is_ground_truth_mask("016_MASK.PNG"))
        self.assertFalse(is_ground_truth_mask("016.png"))

    @patch("anomaly_detector.get_golden_reference", return_value=None)
    @patch("anomaly_detector.match_known_dataset_label", return_value=None)
    @patch("anomaly_detector.predict_model", return_value={"label": "good", "confidence": 0.9})
    def test_detector_uses_bottle_category(self, predict_model, match_label, golden_reference):
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        anomaly_detector.detect_defects(image)

        predict_model.assert_called_once_with(image, category="bottle")
        match_label.assert_called_once_with(image, "bottle")

    def test_load_model_rebuilds_stale_pickle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            old_model = {"version": 999, "labels": ["good", "broken_large"], "feature_count": 1, "sample_counts": {}, "binary_classifiers": {}, "subtype_classifiers": {}}
            stale_path = temp_dir / "defect_model.pkl"
            stale_path.write_bytes(pickle.dumps(old_model))

            original_model_path = defect_model.MODEL_PATH
            original_metadata_path = defect_model.METADATA_PATH
            defect_model.MODEL_PATH = stale_path
            defect_model.METADATA_PATH = temp_dir / "defect_model.json"
            try:
                model = defect_model.load_model()
                self.assertEqual(model["labels"], defect_model.LABELS)
                self.assertEqual(model["version"], defect_model.MODEL_VERSION)
                self.assertEqual(set(model["binary_classifiers"]), {"bottle"})
            finally:
                defect_model.MODEL_PATH = original_model_path
                defect_model.METADATA_PATH = original_metadata_path


if __name__ == "__main__":
    unittest.main()
