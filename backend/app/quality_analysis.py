import cv2
import numpy as np
import os

def analyze_image_quality(image_path: str) -> dict:
    """
    Analyze image quality metrics:
    - Resolution
    - Brightness
    - Sharpness (Laplacian variance)
    - Noise level
    - Overall suitability
    """
    
    img = cv2.imread(image_path)
    if img is None:
        return {
            "status": "error",
            "message": "Could not read image"
        }
    
    height, width = img.shape[:2]
    
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Brightness Analysis (mean pixel value)
    brightness = np.mean(gray)
    if brightness < 50:
        brightness_status = "Too Dark"
    elif brightness > 200:
        brightness_status = "Too Bright"
    elif brightness < 80 or brightness > 180:
        brightness_status = "Acceptable"
    else:
        brightness_status = "Good"
    
    # 2. Sharpness Analysis (Laplacian variance)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 50:
        sharpness_status = "Blurry"
    elif laplacian_var < 100:
        sharpness_status = "Acceptable"
    else:
        sharpness_status = "Good"
    
    # 3. Noise Analysis
    # Estimate noise using median filter difference
    median_filtered = cv2.medianBlur(gray, 5)
    noise = np.mean(np.abs(gray.astype(float) - median_filtered.astype(float)))
    if noise < 5:
        noise_status = "Low"
    elif noise < 15:
        noise_status = "Medium"
    else:
        noise_status = "High"
    
    # 4. Resolution Analysis
    if width < 200 or height < 200:
        resolution_status = "Low"
    elif width < 500 or height < 500:
        resolution_status = "Acceptable"
    else:
        resolution_status = "Good"
    
    # 5. Overall Quality Score
    brightness_score = min(100, max(0, 100 - abs(brightness - 128)))
    sharpness_score = min(100, laplacian_var / 2)
    noise_score = min(100, max(0, 100 - noise * 5))
    resolution_score = min(100, (width * height) / 10000)
    
    overall_score = (brightness_score * 0.3 + sharpness_score * 0.3 + noise_score * 0.2 + resolution_score * 0.2)
    
    if overall_score >= 70:
        overall_status = "Suitable"
        recommendation = "Image is suitable for inspection"
    elif overall_score >= 50:
        overall_status = "Acceptable"
        recommendation = "Image quality is acceptable but could be improved"
    else:
        overall_status = "Poor"
        recommendation = "Please retake the image with better lighting and focus"
    
    return {
        "resolution": {
            "width": width,
            "height": height,
            "status": resolution_status
        },
        "brightness": {
            "value": round(brightness, 2),
            "status": brightness_status
        },
        "sharpness": {
            "value": round(laplacian_var, 2),
            "status": sharpness_status
        },
        "noise": {
            "value": round(noise, 2),
            "status": noise_status
        },
        "overall": {
            "score": round(overall_score, 2),
            "status": overall_status,
            "recommendation": recommendation
        }
    }
