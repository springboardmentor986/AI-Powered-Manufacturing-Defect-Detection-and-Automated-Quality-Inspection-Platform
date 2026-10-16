def get_defect_location_score(defect_type):

    scores = {
        "broken_large": 70,
        "broken_small": 70,
        "contamination": 70
    }

    return scores.get(
        defect_type,
        50
    )