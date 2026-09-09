class DefectTypeScorer:
    """
    Assigns an impact score (0-100) to each defect type.
    """

    DEFECT_TYPE_SCORES = {
        "crack": 95.0,
        "hole": 95.0,
        "cut": 90.0,
        "scratch": 70.0,
        "contamination": 80.0,
        "broken": 95.0,
        "bent": 85.0,
        "deformation": 85.0,
        "color": 60.0,
        "stain": 60.0,
        "rough": 65.0,
        "missing": 90.0,
        "misplaced": 75.0,
        "good": 0.0,
        "normal": 0.0,
        "none": 0.0,
        "unclassified_anomaly": 70.0,
        "anomaly": 70.0,
        "default": 70.0,
    }

    def calculate(self, defect_type: str) -> float:
        if not defect_type:
            raise ValueError(
                "Defect type cannot be empty."
            )

        defect_type = defect_type.lower().strip()

        # 1. Exact match
        if defect_type in self.DEFECT_TYPE_SCORES:
            return self.DEFECT_TYPE_SCORES[defect_type]

        # 2. Normal or good keywords
        if defect_type in ["normal", "good", "none", "ok"]:
            return 0.0

        # 3. Substring keyword matching for compound defect types
        for keyword, score in [
            ("crack", 95.0),
            ("broken", 95.0),
            ("hole", 95.0),
            ("cut", 90.0),
            ("missing", 90.0),
            ("bent", 85.0),
            ("poke", 80.0),
            ("split", 85.0),
            ("squeeze", 80.0),
            ("contamination", 80.0),
            ("scratch", 70.0),
            ("rough", 65.0),
            ("color", 60.0),
            ("glue", 70.0),
            ("thread", 75.0),
            ("imprint", 75.0),
            ("lead", 80.0),
            ("misplaced", 75.0),
            ("stain", 60.0),
        ]:
            if keyword in defect_type:
                return score

        return self.DEFECT_TYPE_SCORES["default"]