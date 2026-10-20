import asyncio
import base64
import gzip
import json
import lzma
import pickle
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import anomaly_detector
from anomaly_detector import calculate_severity, classify_defect
import defect_model
import main
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers
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
                trained_model = {
                    "version": defect_model.MODEL_VERSION,
                    "labels": defect_model.LABELS,
                    "feature_count": 1,
                    "sample_counts": {"good": 1},
                    "binary_classifiers": {"bottle": {}},
                    "subtype_classifiers": {"bottle": {}},
                }
                sample = {"label": "good", "category": "bottle", "path": "sample.png", "features": np.array([0])}
                with patch("defect_model.load_samples", return_value=[sample]):
                    with patch("defect_model.build_model", return_value=trained_model):
                        model = defect_model.load_model()
                self.assertEqual(model["labels"], defect_model.LABELS)
                self.assertEqual(model["version"], defect_model.MODEL_VERSION)
                self.assertEqual(set(model["binary_classifiers"]), {"bottle"})
                self.assertEqual(json.loads(defect_model.METADATA_PATH.read_text())["training_samples"], 1)
            finally:
                defect_model.MODEL_PATH = original_model_path
                defect_model.METADATA_PATH = original_metadata_path

    def test_training_without_dataset_fails_without_writing_empty_model(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_path = Path(tmp_dir) / "defect_model.pkl"
            metadata_path = Path(tmp_dir) / "defect_model.json"
            original_model_path = defect_model.MODEL_PATH
            original_metadata_path = defect_model.METADATA_PATH
            defect_model.MODEL_PATH = model_path
            defect_model.METADATA_PATH = metadata_path
            try:
                with patch("defect_model.load_samples", return_value=[]):
                    with self.assertRaisesRegex(defect_model.ModelNotReadyError, "No bottle training images"):
                        defect_model.train_model()
                self.assertFalse(model_path.exists())
                self.assertFalse(metadata_path.exists())
            finally:
                defect_model.MODEL_PATH = original_model_path
                defect_model.METADATA_PATH = original_metadata_path

    def test_configured_missing_model_returns_clear_not_ready_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_model_path = defect_model.MODEL_PATH
            original_configured = defect_model.MODEL_PATH_IS_CONFIGURED
            defect_model.MODEL_PATH = Path(tmp_dir) / "missing-model.pkl"
            defect_model.MODEL_PATH_IS_CONFIGURED = True
            try:
                with self.assertRaisesRegex(defect_model.ModelNotReadyError, "configured model file was not found"):
                    defect_model.load_model()
            finally:
                defect_model.MODEL_PATH = original_model_path
                defect_model.MODEL_PATH_IS_CONFIGURED = original_configured

    def test_load_model_decodes_render_secret_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_path = Path(tmp_dir) / "defect_model.pkl.xz.b64"
            model_payload = {
                "version": defect_model.MODEL_VERSION,
                "labels": defect_model.LABELS,
                "feature_count": 10020,
                "binary_classifiers": {"bottle": object()},
                "subtype_classifiers": {"bottle": object()},
            }
            encoded_model = base64.b64encode(lzma.compress(pickle.dumps(model_payload)))
            model_path.write_bytes(encoded_model)
            original_model_path = defect_model.MODEL_PATH
            original_configured = defect_model.MODEL_PATH_IS_CONFIGURED
            defect_model.MODEL_PATH = model_path
            defect_model.MODEL_PATH_IS_CONFIGURED = True
            try:
                loaded_model = defect_model.load_model()
                self.assertEqual(loaded_model["feature_count"], 10020)
                self.assertEqual(set(loaded_model["binary_classifiers"]), {"bottle"})
            finally:
                defect_model.MODEL_PATH = original_model_path
                defect_model.MODEL_PATH_IS_CONFIGURED = original_configured

    def test_prediction_rejects_model_without_trained_classifiers(self):
        with self.assertRaisesRegex(defect_model.ModelNotReadyError, "no trained classifiers"):
            defect_model.predict(
                np.zeros((64, 64, 3), dtype=np.uint8),
                model={"binary_classifiers": {}, "subtype_classifiers": {}},
            )

    def test_inspection_reports_unavailable_model_as_503(self):
        _, encoded_image = cv2.imencode(".png", np.zeros((64, 64, 3), dtype=np.uint8))
        upload = UploadFile(
            filename="bottle.png",
            file=BytesIO(encoded_image.tobytes()),
            headers=Headers({"content-type": "image/png"}),
        )
        actor = {"email": "engineer@factory.com", "name": "Test", "role": "Quality Engineer"}
        with patch("main.current_user", return_value=actor):
            with patch("main.detect_defects", side_effect=defect_model.ModelNotReadyError("Model unavailable")):
                with self.assertRaises(HTTPException) as raised:
                    asyncio.run(main.inspect_image(file=upload, authorization="Bearer test"))
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Model unavailable")


if __name__ == "__main__":
    unittest.main()
