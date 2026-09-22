"""
Image preprocessing pipeline for VisionInspect AI.

Covers the Milestone 2 "Image Processing Module" requirements:
- image preprocessing (resize/normalize)
- noise removal
- image enhancement (contrast)
- feature extraction (grayscale representation used downstream)
"""

import cv2
import numpy as np

TARGET_SIZE = (128, 128)


def load_image(path: str):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image at {path}")
    return img


def preprocess(img: np.ndarray) -> np.ndarray:
    """
    Runs the full preprocessing pipeline on a raw BGR image and returns a
    normalized grayscale float32 array in [0, 1], resized to TARGET_SIZE.
    """
    resized = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # noise removal
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # contrast enhancement (CLAHE — adaptive histogram equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # normalize to [0, 1]
    normalized = enhanced.astype(np.float32) / 255.0
    return normalized


def preprocess_path(path: str) -> np.ndarray:
    return preprocess(load_image(path))


def quality_report(img: np.ndarray) -> dict:
    """
    Simple image quality metrics — useful for the 'image quality analysis
    reports' requirement. Works on the raw (pre-resize) image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = float(np.mean(gray))
    return {
        "sharpness": round(float(blur_score), 2),
        "brightness": round(brightness, 2),
        "is_blurry": bool(blur_score < 50),
    }
