"""
Milestone 3 - Weighted severity scoring and pass/fail/review decision.
Weights: Size 30% + Location 25% + Type 25% + Confidence 20%.
Bands: critical >= 80, high >= 60, medium >= 35, else low.
"""
TYPE_WEIGHT = {"crack": 95, "dent": 70, "contamination": 55, "scratch": 40}

def size_score(area_px: int, image_area: int) -> float:
    ratio = area_px / max(image_area, 1)
    return min(100.0, ratio * 4000)  # tuned so a defect covering ~2.5% of the image scores 100

def location_score(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> float:
    """Defects nearer the center of the part score higher (more likely load-bearing / visible)."""
    cx, cy = x + w / 2, y + h / 2
    dx, dy = (cx - img_w / 2) / (img_w / 2), (cy - img_h / 2) / (img_h / 2)
    dist = min(1.0, (dx ** 2 + dy ** 2) ** 0.5)
    return (1 - dist) * 100

def type_score(defect_type: str) -> float:
    return TYPE_WEIGHT.get(defect_type, 50)

def severity_band(score: float) -> str:
    if score >= 80: return "critical"
    if score >= 60: return "high"
    if score >= 35: return "medium"
    return "low"

def score_defect(defect: dict, img_w: int, img_h: int) -> dict:
    s = size_score(defect["area_px"], img_w * img_h)
    l = location_score(defect["bbox_x"], defect["bbox_y"], defect["bbox_w"], defect["bbox_h"], img_w, img_h)
    t = type_score(defect["defect_type"])
    c = defect["confidence"] * 100
    severity = s * 0.30 + l * 0.25 + t * 0.25 + c * 0.20
    defect = dict(defect)
    defect.update({
        "size_score": round(s, 1), "location_score": round(l, 1),
        "type_score": round(t, 1), "confidence_score": round(c, 1),
        "severity_score": round(severity, 1), "severity_level": severity_band(severity),
    })
    return defect

def overall_status(scored_defects: list[dict]) -> str:
    if not scored_defects:
        return "pass"
    if any(d["severity_level"] == "critical" for d in scored_defects):
        return "fail"
    if any(d["severity_level"] in ("high", "medium") for d in scored_defects):
        return "review"
    return "pass"
