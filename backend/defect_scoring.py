def get_defect_type_score(defect_type):

    scores = {
        "broken_large": 95,
        "contamination": 90,
        "broken_small": 70
    }

    return scores.get(
        defect_type,
        50
    )