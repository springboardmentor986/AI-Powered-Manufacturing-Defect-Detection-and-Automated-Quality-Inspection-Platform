"""
Milestone 4 - Lightweight unit tests for the detection + scoring logic.
Run with: python -m pytest tests/  (or `python tests/test_pipeline.py` directly,
since this file also runs standalone with plain asserts - no pytest required).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from app.cv_pipeline import detect_defects
from app.severity import score_defect, severity_band, overall_status
from validation.generate_labeled_dataset import generate_dataset
from validation.evaluate import evaluate, iou


def test_clean_image_has_no_false_positives():
    canvas = np.full((200, 200), 180, dtype=np.uint8)
    defects = detect_defects(canvas)
    assert defects == [], f"Expected no defects on a clean image, got {len(defects)}"


def test_severity_bands():
    assert severity_band(90) == "critical"
    assert severity_band(65) == "high"
    assert severity_band(40) == "medium"
    assert severity_band(10) == "low"


def test_overall_status_logic():
    assert overall_status([]) == "pass"
    assert overall_status([{"severity_level": "low"}]) == "pass"
    assert overall_status([{"severity_level": "medium"}]) == "review"
    assert overall_status([{"severity_level": "critical"}]) == "fail"


def test_iou_perfect_overlap_is_one():
    box = (10, 10, 20, 20)
    assert abs(iou(box, box) - 1.0) < 1e-9


def test_iou_no_overlap_is_zero():
    assert iou((0, 0, 10, 10), (100, 100, 10, 10)) == 0.0


def test_validation_suite_runs_and_scores_well():
    """End-to-end: generate labeled data, run the real pipeline, check it
    scores reasonably well. This is the same thing the Validation & Testing
    page runs live."""
    dataset = generate_dataset(n_images=60, seed=7)
    result = evaluate(dataset)
    assert result["precision"] > 0.8
    assert result["recall"] > 0.8
    assert result["f1"] > 0.8


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
        passed += 1
    print(f"\n{passed}/{len(tests)} tests passed.")
