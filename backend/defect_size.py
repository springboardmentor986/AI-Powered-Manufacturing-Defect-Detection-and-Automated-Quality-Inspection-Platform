def get_defect_size_score(defect_type):

    scores = {
        "broken_large": 95,
        "broken_small": 55,
        "contamination": 70
    }

    return scores.get(
        defect_type,
        50
    )