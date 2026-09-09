class SizeScorer:
    """
    Converts predicted defect area (%) into a Size Score (0-100).

    The score represents the relative extent of the predicted
    defective region for the given category.
    """

    def __init__(self, boundaries):
        self.boundaries = boundaries

    def calculate(self, category, predicted_area_percent):

        if category not in self.boundaries:
            raise ValueError(
                f"No size boundaries found for category: {category}"
            )

        values = self.boundaries[category]

        p10 = values["p10"]
        p25 = values["p25"]
        p50 = values["p50"]
        p75 = values["p75"]
        p90 = values["p90"]
        p95 = values["p95"]

        area = float(predicted_area_percent)

        points = [
            (p10, 10.0),
            (p25, 25.0),
            (p50, 50.0),
            (p75, 75.0),
            (p90, 90.0),
            (p95, 100.0),
        ]

        if area <= p10:
            return 0.0

        for i in range(len(points) - 1):

            lower_area, lower_score = points[i]
            upper_area, upper_score = points[i + 1]

            if area <= upper_area:

                if upper_area == lower_area:
                    return upper_score

                ratio = (
                    (area - lower_area)
                    / (upper_area - lower_area)
                )

                score = (
                    lower_score
                    + ratio * (upper_score - lower_score)
                )

                return float(score)

        return 100.0