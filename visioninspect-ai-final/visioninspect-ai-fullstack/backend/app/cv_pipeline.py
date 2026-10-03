"""
Milestone 2 - Classical computer-vision defect detection pipeline (OpenCV).
Mirrors the in-browser JS pipeline exactly, so results are consistent between
the demo (client-side) and this backend (server-side):

  1. Bilateral filter   - edge-preserving denoise (keeps thin 1-2px scratches,
                           unlike a median blur which erases them)
  2. CLAHE               - local contrast boost so faint defects stand out
  3. Sobel edge detection (RAW magnitude, not normalized - normalizing per
                           image caused false positives on clean surfaces)
  4. Absolute threshold  - ~140 on the raw Sobel magnitude
  5. Morphological close - joins broken edge fragments into solid regions
  6. Connected components - group defect pixels into candidate regions
  7. Shape classification - solidity / extent / aspect ratio ->
                           crack | scratch | dent | contamination
"""
import cv2
import numpy as np

SOBEL_THRESHOLD = 140
MIN_AREA_PX = 40


def detect_defects(gray: np.ndarray) -> list[dict]:
    """gray: single-channel uint8 image. Returns a list of raw defect dicts."""
    denoised = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)

    gx = cv2.Sobel(contrast, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(contrast, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)  # NOT normalized - see module docstring

    _, mask = cv2.threshold(magnitude, SOBEL_THRESHOLD, 255, cv2.THRESH_BINARY)
    mask = mask.astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    defects = []
    for label in range(1, n_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < MIN_AREA_PX:
            continue
        x, y, w, h = (int(stats[label, i]) for i in
                      (cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT))
        component_mask = (labels[y:y+h, x:x+w] == label).astype(np.uint8)
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        contour = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(contour)
        hull_area = max(cv2.contourArea(hull), 1.0)
        contour_area = max(cv2.contourArea(contour), 1.0)
        solidity = contour_area / hull_area
        extent = area / max(w * h, 1)
        aspect = max(w, h) / max(min(w, h), 1)
        perimeter = cv2.arcLength(contour, True)
        circularity = (perimeter ** 2) / (4 * np.pi * contour_area)  # 1.0 = perfect circle, higher = more jagged

        defect_type, confidence = classify_shape(solidity, extent, aspect, circularity)
        defects.append({
            "bbox_x": x, "bbox_y": y, "bbox_w": w, "bbox_h": h,
            "area_px": area, "defect_type": defect_type, "confidence": confidence,
            "solidity": round(solidity, 3), "extent": round(extent, 3), "aspect": round(aspect, 3),
            "circularity": round(circularity, 3),
        })
    return defects


def classify_shape(solidity: float, extent: float, aspect: float, circularity: float) -> tuple[str, float]:
    """Decision tree, in order:
      1. Very elongated (aspect >= 5)              -> scratch  (long thin line)
      2. Compact + near-circular boundary (<1.23)   -> dent     (smooth rounded impact)
      3. Compact + somewhat irregular (<1.5)         -> contamination (patchy, textured residue)
      4. Everything else jagged/thin                -> crack

    Crack vs dent/contamination is the fuzziest boundary - a deep, narrow
    crack can look compact at low resolution. This is a known, documented
    limitation rather than hidden."""
    if aspect >= 5:
        return "scratch", min(0.98, 0.70 + (aspect - 5) * 0.02)
    if extent < 0.5:
        if circularity < 1.23:
            return "dent", max(0.6, 0.95 - (circularity - 1.0) * 1.0)
        if circularity < 1.5:
            return "contamination", max(0.6, 0.90 - (circularity - 1.23) * 0.5)
    if aspect >= 2.5 and solidity > 0.55:
        return "scratch", 0.65 + min(0.2, (aspect - 2.5) * 0.05)
    return "crack", max(0.6, min(0.95, 0.55 + circularity * 0.04))


def annotate(bgr_image: np.ndarray, defects_with_scores: list[dict]) -> np.ndarray:
    """Draw bounding boxes colored by severity level onto a copy of the image."""
    colors = {"critical": (0, 0, 220), "high": (0, 140, 255), "medium": (210, 180, 60), "low": (90, 200, 90)}
    out = bgr_image.copy()
    for d in defects_with_scores:
        color = colors.get(d["severity_level"], (200, 200, 200))
        x, y, w, h = d["bbox_x"], d["bbox_y"], d["bbox_w"], d["bbox_h"]
        cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
        label = f"{d['defect_type']} {d['severity_score']:.0f}"
        cv2.putText(out, label, (x, max(12, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    return out
