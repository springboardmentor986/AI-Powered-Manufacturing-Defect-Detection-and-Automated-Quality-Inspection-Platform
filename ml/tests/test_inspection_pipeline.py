import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from inference import inspection_pipeline as pipeline


def test_retrained_yolo_models_are_used_for_carpet_and_wood():
    assert "bottle_defect_improved" in str(
        pipeline.get_yolo_model_path("bottle")
    )
    assert pipeline.get_yolo_model_path("carpet").name == "best.pt"
    assert "carpet_defect_" in str(pipeline.get_yolo_model_path("carpet"))
    assert "wood_defect_" in str(pipeline.get_yolo_model_path("wood"))
    assert pipeline.YOLO_CONFIDENCE == 0.10
    assert pipeline.CATEGORY_YOLO_CONFIDENCE["toothbrush"] == 0.35
    assert pipeline.CATEGORY_YOLO_CONFIDENCE["transistor"] == 0.35
    assert pipeline.CATEGORY_YOLO_CONFIDENCE["carpet"] == 0.25


@pytest.fixture
def image_path(tmp_path):
    image = tmp_path / "sample.png"
    image = str(image)
    assert cv2.imwrite(image, np.zeros((32, 32, 3), dtype=np.uint8))
    return image


def test_inspect_image_skips_yolo_when_autoencoder_marks_good(monkeypatch, image_path):
    monkeypatch.setattr(pipeline, "load_thresholds", lambda: {"bottle": 0.1})
    monkeypatch.setattr(pipeline, "get_category_threshold", lambda thresholds, category: 0.1)
    monkeypatch.setattr(pipeline, "load_autoencoder", lambda category: object())
    monkeypatch.setattr(pipeline, "preprocess_image", lambda path: object())
    monkeypatch.setattr(pipeline, "detect_anomaly", lambda model, tensor, threshold: ("GOOD", 0.01))

    called = {"yolo": False}

    def fake_localize(category, image):
        called["yolo"] = True
        return []

    monkeypatch.setattr(pipeline, "localize_defect", fake_localize)

    result = pipeline.inspect_image(image_path, "bottle")

    assert result["status"] == "GOOD"
    assert called["yolo"] is False


def test_preprocess_image_uses_training_preprocessing(monkeypatch, tmp_path):
    image_path = tmp_path / "sample.png"
    normalized = np.zeros((224, 224, 3), dtype=np.float32)
    called = {"path": None}

    def fake_preprocess(path):
        called["path"] = path
        return normalized, {}

    monkeypatch.setattr(
        pipeline,
        "preprocess_training_image",
        fake_preprocess,
    )

    tensor = pipeline.preprocess_image(image_path)

    assert called["path"] == image_path
    assert tuple(tensor.shape) == (1, 3, 224, 224)


def test_inspect_image_runs_yolo_after_autoencoder_detects_defect(monkeypatch, image_path):
    monkeypatch.setattr(pipeline, "load_thresholds", lambda: {"bottle": 0.1})
    monkeypatch.setattr(pipeline, "get_category_threshold", lambda thresholds, category: 0.1)
    monkeypatch.setattr(pipeline, "load_autoencoder", lambda category: object())
    monkeypatch.setattr(pipeline, "preprocess_image", lambda path: object())
    monkeypatch.setattr(pipeline, "detect_anomaly", lambda model, tensor, threshold: ("DEFECT", 0.5))

    called = {"yolo": False, "classify": False}

    def fake_localize(category, image):
        called["yolo"] = True
        return [{
            "confidence": 0.9,
            "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        }]

    def fake_classify(category, image, bbox=None):
        called["classify"] = True
        return {"defect_type": "scratch", "confidence": 0.87, "model": "test_model"}

    monkeypatch.setattr(pipeline, "localize_defect", fake_localize)
    monkeypatch.setattr(pipeline, "classify_defect", fake_classify)
    monkeypatch.setattr(pipeline, "assess_quality", lambda image_path, detection: {
        "severity": {"score": 75, "level": "High", "components": {"size": 0, "location": 0, "defect_type": 0, "confidence": 0}},
        "quality_decision": "FAIL",
        "recommendation": "Manual inspection required."
    })

    result = pipeline.inspect_image(image_path, "bottle")

    assert result["status"] == "DEFECT"
    assert called["yolo"] is True
    assert called["classify"] is True
    assert result["defects"][0]["defect_type"] == "scratch"


def test_localize_defect_rejects_white_margin_on_dark_product(monkeypatch, tmp_path):
    image_path = tmp_path / "zipper.png"
    image = np.full((200, 200, 3), 255, dtype=np.uint8)
    image[:, 60:140] = 35
    assert cv2.imwrite(str(image_path), image)

    class FakeTensor:
        def __init__(self, values):
            self.values = values

        def cpu(self):
            return self

        def numpy(self):
            return np.array(self.values, dtype=np.float32)

        def item(self):
            return self.values

    class FakeBox:
        def __init__(self, coordinates, confidence):
            self.xyxy = [FakeTensor(coordinates)]
            self.conf = [FakeTensor(confidence)]

    class FakeResult:
        boxes = [
            FakeBox([5, 40, 45, 90], 0.8),
            FakeBox([75, 80, 105, 120], 0.7),
        ]

    class FakeYOLO:
        def __init__(self, path):
            self.path = path

        def predict(self, **kwargs):
            return [FakeResult()]

    model_path = (
        pipeline.YOLO_DIR
        / "runs"
        / "zipper_defect"
        / "weights"
        / "best.pt"
    )
    monkeypatch.setattr(pipeline, "YOLO", FakeYOLO)
    monkeypatch.setattr(Path, "exists", lambda path: path == model_path)

    detections = pipeline.localize_defect("zipper", image_path)

    assert len(detections) == 1
    assert detections[0]["bbox"]["x1"] == 75


def test_weak_category_filters_reject_edge_background_boxes(monkeypatch, tmp_path):
    image_path = tmp_path / "category.png"
    image = np.full((200, 200, 3), 120, dtype=np.uint8)
    assert cv2.imwrite(str(image_path), image)

    class FakeTensor:
        def __init__(self, values):
            self.values = values

        def cpu(self):
            return self

        def numpy(self):
            return np.array(self.values, dtype=np.float32)

        def item(self):
            return self.values

    class FakeBox:
        def __init__(self, coordinates, confidence):
            self.xyxy = [FakeTensor(coordinates)]
            self.conf = [FakeTensor(confidence)]

    class FakeResult:
        boxes = [
            FakeBox([0, 40, 40, 100], 0.6),
            FakeBox([80, 80, 120, 130], 0.6),
        ]

    class FakeYOLO:
        def __init__(self, path):
            self.path = path

        def predict(self, **kwargs):
            return [FakeResult()]

    model_path = (
        pipeline.YOLO_DIR
        / "runs"
        / "toothbrush_defect_retrained"
        / "weights"
        / "best.pt"
    )
    monkeypatch.setattr(pipeline, "YOLO", FakeYOLO)
    monkeypatch.setattr(Path, "exists", lambda path: path == model_path)

    detections = pipeline.localize_defect("toothbrush", image_path)

    assert len(detections) == 1
    assert detections[0]["bbox"]["x1"] == 80


def test_localize_defect_returns_no_box_when_yolo_has_no_box(
    monkeypatch,
    tmp_path,
):
    image_path = tmp_path / "screw.png"
    image = np.full((200, 200, 3), 240, dtype=np.uint8)
    image[50:150, 80:120] = 80
    assert cv2.imwrite(str(image_path), image)

    class EmptyYOLO:
        def __init__(self, path):
            self.path = path

        def predict(self, **kwargs):
            return [type("Result", (), {"boxes": []})()]

    model_path = (
        pipeline.YOLO_DIR
        / "runs"
        / "screw_defect_retrained"
        / "weights"
        / "best.pt"
    )
    monkeypatch.setattr(pipeline, "YOLO", EmptyYOLO)
    monkeypatch.setattr(Path, "exists", lambda path: path == model_path)

    detections = pipeline.localize_defect("screw", image_path)

    assert detections == []
