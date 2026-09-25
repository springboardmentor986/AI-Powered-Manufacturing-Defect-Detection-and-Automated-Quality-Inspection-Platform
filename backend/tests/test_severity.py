import pytest

from ml.severity import (
    DEFECT_TYPE_SEVERITY,
    get_defect_type_score,
    calculate_severity,
    check_confidence,
    assess_quality,
)


# ============================================================
# get_defect_type_score()
# ============================================================

def test_get_defect_type_score():
    """Known defect type should return the correct severity score."""
    assert get_defect_type_score("crack") == 85.0


def test_get_defect_type_score_unknown():
    """Unknown defect type should raise ValueError."""
    with pytest.raises(ValueError):
        get_defect_type_score("unknown_defect")


def test_all_defect_scores_are_valid():
    """Every configured defect severity score should be between 0 and 100."""
    for defect_type, score in DEFECT_TYPE_SEVERITY.items():
        assert 0 <= score <= 100, (
            f"{defect_type} has invalid score: {score}"
        )


# ============================================================
# calculate_severity()
# ============================================================

def test_calculate_severity_formula():
    """Check the severity formula."""
    result = calculate_severity(
        size=80,
        location=60,
        defect_type=70,
        confidence=90,
    )

    expected = (
        (80 * 0.30)
        + (60 * 0.25)
        + (70 * 0.25)
        + (90 * 0.20)
    )

    assert result["severity_score"] == round(expected, 2)


def test_critical_severity():
    """Score >= 80 should be Critical and Reject."""
    result = calculate_severity(
        size=100,
        location=100,
        defect_type=100,
        confidence=100,
    )

    assert result["severity_score"] == 100
    assert result["severity_level"] == "Critical"
    assert result["recommended_action"] == "Reject"


def test_high_severity():
    """Score between 60 and 79.99 should be High and Rework."""
    result = calculate_severity(
        size=70,
        location=60,
        defect_type=70,
        confidence=70,
    )

    assert 60 <= result["severity_score"] < 80
    assert result["severity_level"] == "High"
    assert result["recommended_action"] == "Rework"


def test_medium_severity():
    """Score between 40 and 59.99 should be Medium and Review."""
    result = calculate_severity(
        size=50,
        location=40,
        defect_type=50,
        confidence=50,
    )

    assert 40 <= result["severity_score"] < 60
    assert result["severity_level"] == "Medium"
    assert result["recommended_action"] == "Review"


def test_low_severity():
    """Score below 40 should be Low and Accept."""
    result = calculate_severity(
        size=10,
        location=10,
        defect_type=10,
        confidence=10,
    )

    assert result["severity_score"] < 40
    assert result["severity_level"] == "Low"
    assert result["recommended_action"] == "Accept"




def test_high_confidence():
    result = check_confidence(85)

    assert result["confidence_score"] == 85
    assert result["manual_review"] is False


def test_low_confidence():
    result = check_confidence(65)

    assert result["confidence_score"] == 65
    assert result["manual_review"] is True


def test_confidence_exactly_70():
    result = check_confidence(70)

    assert result["confidence_score"] == 70
    assert result["manual_review"] is False




def test_quality_pass():
    result = assess_quality(
        defect_type="scratch",
        classification_confidence=90,
        severity_score=30,
        severity_level="Low",
        recommended_action="Accept",
    )

    assert result["quality_status"] == "PASS"
    assert result["manual_review"] is False


def test_quality_review():
    result = assess_quality(
        defect_type="scratch",
        classification_confidence=90,
        severity_score=50,
        severity_level="Medium",
        recommended_action="Review",
    )

    assert result["quality_status"] == "REVIEW"
    assert result["manual_review"] is False


def test_quality_rework():
    result = assess_quality(
        defect_type="crack",
        classification_confidence=90,
        severity_score=70,
        severity_level="High",
        recommended_action="Rework",
    )

    assert result["quality_status"] == "REWORK"
    assert result["manual_review"] is False


def test_quality_fail():
    result = assess_quality(
        defect_type="broken_large",
        classification_confidence=95,
        severity_score=90,
        severity_level="Critical",
        recommended_action="Reject",
    )

    assert result["quality_status"] == "FAIL"
    assert result["manual_review"] is False




def test_low_classification_confidence_forces_manual_review():
    result = assess_quality(
        defect_type="crack",
        classification_confidence=60,
        severity_score=90,
        severity_level="Critical",
        recommended_action="Reject",
    )

    assert result["quality_status"] == "MANUAL_REVIEW"
    assert result["recommended_action"] == "MANUAL_REVIEW"
    assert result["manual_review"] is True


def test_confidence_70_does_not_force_manual_review():
    result = assess_quality(
        defect_type="crack",
        classification_confidence=70,
        severity_score=90,
        severity_level="Critical",
        recommended_action="Reject",
    )

    assert result["quality_status"] == "FAIL"
    assert result["recommended_action"] == "Reject"
    assert result["manual_review"] is False




def test_confidence_is_rounded():
    
    result = check_confidence(75.6789)

    assert result["confidence_score"] == 75.68


def test_severity_is_rounded():
    result = calculate_severity(
        size=73.333,
        location=61.111,
        defect_type=82.222,
        confidence=91.999,
    )

    expected = (
        (73.333 * 0.30)
        + (61.111 * 0.25)
        + (82.222 * 0.25)
        + (91.999 * 0.20)
    )

    assert result["severity_score"] == round(expected, 2)