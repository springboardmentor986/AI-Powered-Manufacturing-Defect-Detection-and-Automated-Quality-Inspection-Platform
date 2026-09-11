import cv2
import numpy as np


def analyze_image_quality(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return {
            "success": False,
            "message": "Unable to read image"
        }

    height, width = image.shape[:2]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Brightness
    brightness = float(np.mean(gray))

    # Contrast
    contrast = float(np.std(gray))

    # Blur detection using Laplacian variance
    blur_score = float(
        cv2.Laplacian(gray, cv2.CV_64F).var()
    )

    # Determine blur status
    if blur_score < 100:
        blur_status = "BLURRY"
    else:
        blur_status = "SHARP"

    # Determine brightness status
    if brightness < 60:
        brightness_status = "DARK"
    elif brightness > 200:
        brightness_status = "OVEREXPOSED"
    else:
        brightness_status = "GOOD"

    # Quality score
    quality_score = 100

    if blur_score < 100:
        quality_score -= 30

    if brightness < 60 or brightness > 200:
        quality_score -= 20

    if contrast < 20:
        quality_score -= 20

    quality_score = max(0, quality_score)

    if quality_score >= 80:
        quality_status = "GOOD"
    elif quality_score >= 50:
        quality_status = "ACCEPTABLE"
    else:
        quality_status = "POOR"

    return {
        "success": True,
        "width": width,
        "height": height,
        "resolution": f"{width} x {height}",
        "brightness": round(brightness, 2),
        "brightness_status": brightness_status,
        "contrast": round(contrast, 2),
        "blur_score": round(blur_score, 2),
        "blur_status": blur_status,
        "quality_score": quality_score,
        "quality_status": quality_status
    }