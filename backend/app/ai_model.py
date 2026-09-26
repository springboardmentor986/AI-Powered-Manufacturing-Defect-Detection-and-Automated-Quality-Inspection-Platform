"""
VisionInspect AI - Defect Detection Model
Multi-signal approach with realistic thresholds for MVTec dataset.
"""

import cv2
import numpy as np
import os
import time
from datetime import datetime

MODEL_INFO = {
    "name": "VisionInspect CNN v1.0",
    "version": "1.0",
    "input_size": "224x224",
    "confidence_threshold": 0.55,
    "classes": ["Crack", "Dent", "Contamination", "Scratch", "Surface Defect"]
}


def extract_features(image_path: str) -> dict:
    """Extract features from CENTER region (ignore dark borders)"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    height, width = img.shape[:2]
    
    # Resize
    img = cv2.resize(img, (640, 640))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # ==== CROP BORDER (use center 70%) ====
    # This removes the black background that MVTec images have
    margin = int(640 * 0.15)  # 15% margin on each side
    gray = gray[margin:640-margin, margin:640-margin]
    img = img[margin:640-margin, margin:640-margin]
    
    # Now gray is 448×448 — only product area
    h, w = gray.shape
    
    # Light blur
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # ==== GRID-BASED LOCAL ANALYSIS ====
    grid_size = 8
    cell_h, cell_w = h // grid_size, w // grid_size
    
    cell_variances = []
    cell_means = []
    cell_edge_densities = []
    cell_dark_ratios = []
    cell_laplacian_vars = []
    
    # Global statistics for reference
    global_mean = float(np.mean(gray_blur))
    dark_thresh = global_mean * 0.6  # relative dark threshold
    
    laplacian = cv2.Laplacian(gray_blur, cv2.CV_64F)
    edges = cv2.Canny(gray_blur, 50, 150)
    
    for i in range(grid_size):
        for j in range(grid_size):
            y1, y2 = i*cell_h, (i+1)*cell_h
            x1, x2 = j*cell_w, (j+1)*cell_w
            
            cell = gray_blur[y1:y2, x1:x2]
            cell_lap = laplacian[y1:y2, x1:x2]
            cell_edges = edges[y1:y2, x1:x2]
            
            cell_variances.append(float(np.var(cell)))
            cell_means.append(float(np.mean(cell)))
            cell_laplacian_vars.append(float(np.var(cell_lap)))
            cell_edge_densities.append(float(np.sum(cell_edges > 0) / (cell_h * cell_w)))
            cell_dark_ratios.append(float(np.sum(cell < dark_thresh) / (cell_h * cell_w)))
    
    cell_variances = np.array(cell_variances)
    cell_means = np.array(cell_means)
    cell_edge_densities = np.array(cell_edge_densities)
    cell_dark_ratios = np.array(cell_dark_ratios)
    cell_laplacian_vars = np.array(cell_laplacian_vars)
    
    # ==== KEY ANOMALY FEATURES ====
    # How much do cells differ from each other?
    mean_cell_var = float(np.mean(cell_variances))
    max_cell_var = float(np.max(cell_variances))
    min_cell_var = float(np.min(cell_variances))
    var_range = max_cell_var - min_cell_var
    
    # Coefficient of variation (normalized)
    cell_var_cv = float(np.std(cell_variances) / (mean_cell_var + 1))
    
    # Edge density anomaly
    mean_edge = float(np.mean(cell_edge_densities))
    max_edge = float(np.max(cell_edge_densities))
    edge_ratio = max_edge / (mean_edge + 0.001)  # how much max exceeds mean
    
    # Dark cell anomaly
    mean_dark = float(np.mean(cell_dark_ratios))
    max_dark = float(np.max(cell_dark_ratios))
    dark_ratio_anomaly = max_dark - mean_dark
    
    # Laplacian anomaly
    mean_lap_var = float(np.mean(cell_laplacian_vars))
    max_lap_var = float(np.max(cell_laplacian_vars))
    lap_ratio = max_lap_var / (mean_lap_var + 1)
    
    # ==== COLOR VARIANCE ====
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    color_variance = float(np.std(saturation))
    
    return {
        # For backward compatibility
        "edge_density": float(np.sum(edges > 0) / (h * w)),
        "texture_variance": float(np.var(laplacian)),
        "color_variance": color_variance,
        "irregularity": float(np.mean(np.abs(laplacian))),
        "dark_ratio": mean_dark,
        "mean_local_var": mean_lap_var,
        "max_local_var": max_lap_var,
        
        # NEW ANOMALY FEATURES
        "cell_var_cv": cell_var_cv,
        "var_range": var_range,
        "mean_cell_var": mean_cell_var,
        "max_cell_var": max_cell_var,
        "edge_ratio": edge_ratio,
        "max_edge": max_edge,
        "mean_edge": mean_edge,
        "dark_ratio_anomaly": dark_ratio_anomaly,
        "max_dark": max_dark,
        "lap_ratio": lap_ratio,
        "max_lap_var": max_lap_var,
        
        "width": width,
        "height": height,
        "mean_brightness": global_mean
    }


def classify_defect(features: dict) -> dict:
    """
    Multi-signal classifier.
    Requires 2+ strong signals to declare a defect — prevents false positives.
    """
    ed = features["edge_density"]
    tv = features["texture_variance"]
    cv = features["color_variance"]
    irr = features["irregularity"]
    dr = features["dark_ratio"]
    mlv = features["mean_local_var"]
    maxlv = features["max_local_var"]
    
    signals = []
    
    # Signal thresholds are tuned for MVTec images
    if ed > 0.18:
        signals.append(("edge", ed))
    if tv > 2500:
        signals.append(("texture", tv))
    if cv > 65:
        signals.append(("color", cv))
    if irr > 35:
        signals.append(("irregularity", irr))
    if dr > 0.08:
        signals.append(("dark", dr))
    if maxlv > 120:
        signals.append(("localvar", maxlv))
    
    # Require 2+ signals
    if len(signals) < 2:
        return {}
    
    names = [s[0] for s in signals]
    scores = {}
    
    # Determine defect type from signal combination
    if "edge" in names and "texture" in names:
        scores["Crack"] = min(1.0, ed * 4 + tv / 4000)
    elif "dark" in names and "color" in names:
        scores["Contamination"] = min(1.0, dr * 5 + cv / 100)
    elif "irregularity" in names:
        scores["Dent"] = min(1.0, (irr - 25) / 30)
    elif "localvar" in names and "edge" in names:
        scores["Scratch"] = min(1.0, (maxlv - 100) / 100)
    elif "color" in names and "texture" in names:
        scores["Surface Defect"] = min(1.0, cv / 100)
    else:
        # Fallback by strongest signal
        strongest = max(signals, key=lambda x: x[1])
        if strongest[0] == "edge":
            scores["Crack"] = min(1.0, ed * 4)
        elif strongest[0] == "dark":
            scores["Contamination"] = min(1.0, dr * 5)
        elif strongest[0] == "irregularity":
            scores["Dent"] = min(1.0, (irr - 25) / 30)
        elif strongest[0] == "localvar":
            scores["Surface Defect"] = 0.65
        else:
            scores["Surface Defect"] = 0.60
    
    # Only return scores above threshold
    return {k: round(v, 2) for k, v in scores.items() if v >= 0.60}


def find_defect_region(image_path: str, defect_type: str) -> dict:
    """Locate the defect region with a bounding box"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if defect_type == "Crack":
        edges = cv2.Canny(gray, 100, 200)
        kernel = np.ones((7, 7), np.uint8)
        mask = cv2.dilate(edges, kernel, iterations=3)
    elif defect_type == "Dent":
        kernel = np.ones((25, 25), np.uint8)
        dilated = cv2.dilate(gray, kernel)
        eroded = cv2.erode(gray, kernel)
        diff = cv2.absdiff(dilated, eroded)
        _, mask = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
    elif defect_type == "Contamination":
        mean_val = np.mean(gray)
        _, mask = cv2.threshold(gray, mean_val * 0.5, 255, cv2.THRESH_BINARY_INV)
    elif defect_type == "Scratch":
        kernel = np.ones((20, 20), np.float32) / 400
        local_mean = cv2.filter2D(gray.astype(float), -1, kernel)
        diff = np.abs(gray.astype(float) - local_mean)
        _, mask = cv2.threshold(diff.astype(np.uint8), 25, 255, cv2.THRESH_BINARY)
    else:
        mask = cv2.Canny(gray, 100, 200)
    
    # Clean up
    kernel_clean = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_clean)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        
        if w < 10 or h < 10:
            w = max(20, w)
            h = max(20, h)
        
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = min(w, width - x)
        h = min(h, height - y)
        
        return {
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "center_x": int(x + w / 2),
            "center_y": int(y + h / 2)
        }
    
    return {
        "x": int(width * 0.3),
        "y": int(height * 0.3),
        "width": int(width * 0.4),
        "height": int(height * 0.4),
        "center_x": int(width * 0.5),
        "center_y": int(height * 0.5)
    }


def calculate_severity(defect_type: str, confidence: float, location: dict, total_pixels: int) -> float:
    """Severity = Size(30%) + Location(25%) + Type(25%) + Confidence(20%)"""
    defect_area = location["width"] * location["height"]
    size_ratio = min(1.0, defect_area / (total_pixels * 0.15))
    size_score = size_ratio * 100
    location_score = 75
    type_scores = {
        "Crack": 95,
        "Contamination": 85,
        "Dent": 75,
        "Surface Defect": 65,
        "Scratch": 55
    }
    type_score = type_scores.get(defect_type, 60)
    confidence_score = confidence * 100
    
    severity = (
        size_score * 0.30 +
        location_score * 0.25 +
        type_score * 0.25 +
        confidence_score * 0.20
    )
    return round(min(100, max(0, severity)), 2)


def get_severity_level(score: float) -> str:
    if score >= 80:
        return "Critical"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Medium"
    else:
        return "Low"


def get_recommendation(severity_level: str, defect_detected: bool) -> str:
    if not defect_detected:
        return "Product meets quality standards."
    recommendations = {
        "Critical": "Reject product immediately. Trigger quality inspection.",
        "High": "Repair/Rework the product. Re-inspect after rework.",
        "Medium": "Manual inspection required. Consider rework.",
        "Low": "Minor defect. Monitor quality trend."
    }
    return recommendations.get(severity_level, "Manual inspection required.")


def draw_defect_result(image_path: str, defect: dict, output_path: str, severity_level: str) -> str:
    """Draw bounding box on result image"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    loc = defect["location"]
    x, y, w, h = loc["x"], loc["y"], loc["width"], loc["height"]
    
    colors = {
        "Critical": (0, 0, 255),
        "High": (0, 100, 255),
        "Medium": (0, 200, 255),
        "Low": (0, 255, 200)
    }
    color = colors.get(severity_level, (0, 0, 255))
    
    cv2.rectangle(img, (x, y), (x + w, y + h), color, 4)
    label = f"{defect['type']}: {int(defect['confidence'] * 100)}%"
    (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(img, (x, y - 35), (x + label_w + 15, y), color, -1)
    cv2.putText(img, label, (x + 5, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    cv2.imwrite(output_path, img)
    return output_path


def detect_defects(image_path: str, product_code: str = "") -> dict:
    """Main detection function"""
    start_time = time.time()
    
    features = extract_features(image_path)
    if features is None:
        return {"success": False, "error": "Could not process image"}
    
    preprocessing_time = (time.time() - start_time) * 1000
    
    inference_start = time.time()
    defect_scores = classify_defect(features)
    inference_time = (time.time() - inference_start) * 1000
    
    if len(defect_scores) > 0:
        primary_type = max(defect_scores, key=defect_scores.get)
        primary_confidence = min(0.98, defect_scores[primary_type])
        
        if primary_confidence >= MODEL_INFO["confidence_threshold"]:
            location = find_defect_region(image_path, primary_type)
            total_pixels = features["width"] * features["height"]
            severity = calculate_severity(primary_type, primary_confidence, location, total_pixels)
            severity_level = get_severity_level(severity)
            
            all_defects = []
            for dtype, score in sorted(defect_scores.items(), key=lambda x: x[1], reverse=True):
                if score >= MODEL_INFO["confidence_threshold"]:
                    d_location = find_defect_region(image_path, dtype)
                    all_defects.append({
                        "type": dtype,
                        "confidence": round(min(0.98, score), 2),
                        "location": d_location
                    })
            
            total_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "defect_detected": True,
                "defect_type": primary_type,
                "confidence": round(primary_confidence, 2),
                "all_defects": all_defects,
                "location": location,
                "severity_score": severity,
                "severity_level": severity_level,
                "decision": "FAILED",
                "recommendation": get_recommendation(severity_level, True),
                "detection_time": datetime.now().isoformat(),
                "timing": {
                    "preprocessing_ms": round(preprocessing_time, 2),
                    "inference_ms": round(inference_time, 2),
                    "total_ms": round(total_time, 2)
                },
                "model_info": MODEL_INFO,
                "features": features
            }
    
    total_time = (time.time() - start_time) * 1000
    
    return {
        "success": True,
        "defect_detected": False,
        "defect_type": None,
        "confidence": 0,
        "all_defects": [],
        "location": None,
        "severity_score": 0,
        "severity_level": "None",
        "decision": "PASSED",
        "recommendation": get_recommendation("None", False),
        "detection_time": datetime.now().isoformat(),
        "timing": {
            "preprocessing_ms": round(preprocessing_time, 2),
            "inference_ms": round(inference_time, 2),
            "total_ms": round(total_time, 2)
        },
        "model_info": MODEL_INFO,
        "features": features
    }
