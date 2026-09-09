import numpy as np


class LocationScorer:
    """Calculates Location Score (0-100) combining defect centroid distance and area."""

    def calculate(self, defect_mask: np.ndarray) -> float:
        if defect_mask is None:
            raise ValueError("Defect mask cannot be None.")
        if defect_mask.ndim != 2:
            raise ValueError("Defect mask must be a 2D array.")

        defect_pixels = np.argwhere(defect_mask > 0)
        if len(defect_pixels) == 0:
            return 0.0

        height, width = defect_mask.shape
        centroid_y = defect_pixels[:, 0].mean()
        centroid_x = defect_pixels[:, 1].mean()

        center_x = width / 2.0
        center_y = height / 2.0

        distance = np.sqrt((centroid_x - center_x) ** 2 + (centroid_y - center_y) ** 2)
        max_distance = np.sqrt(center_x ** 2 + center_y ** 2)

        center_score = np.clip((1.0 - distance / max_distance) * 100.0, 0.0, 100.0)
        area_percentage = (len(defect_pixels) / defect_mask.size) * 100.0
        area_score = np.clip(area_percentage * 10.0, 0.0, 100.0)

        location_score = center_score * 0.7 + area_score * 0.3
        return float(np.clip(location_score, 0.0, 100.0))