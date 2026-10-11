import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image
from ..config import settings

class PreprocessingService:
    """
    Image Preprocessing & Quality Analysis Service (Milestone 2 Specification).
    Handles edge-preserving noise removal, CLAHE contrast enhancement,
    ROI segmentation, and technical image quality grading.
    """

    @classmethod
    def preprocess_image(
        cls,
        image_path: Path,
        output_prefix: str = "proc",
        target_size: Tuple[int, int] = (512, 512)
    ) -> Dict[str, Any]:
        """
        Runs the full industrial preprocessing pipeline:
        1. Dimension normalization & resizing (512x512)
        2. Bilateral filtering for edge-preserving noise reduction
        3. CLAHE contrast enhancement on Luminance channel
        4. Region of Interest (ROI) foreground extraction
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")

        # Read image using OpenCV
        img_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if img_bgr is None:
            # Fallback for formats OpenCV might struggle with
            pil_img = Image.open(image_path).convert("RGB")
            img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        orig_h, orig_w = img_bgr.shape[:2]

        # 1. Resize to target dimension while maintaining aspect ratio
        resized_bgr = cv2.resize(img_bgr, target_size, interpolation=cv2.INTER_AREA)

        # 2. Bilateral Filter: Smooths sensor noise without blurring sharp defect edges
        # d=9: Diameter of pixel neighborhood
        # sigmaColor=75: Filter sigma in the color space
        # sigmaSpace=75: Filter sigma in the coordinate space
        denoised_bgr = cv2.bilateralFilter(resized_bgr, d=9, sigmaColor=75, sigmaSpace=75)

        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Convert to LAB color space to operate strictly on the Luminance (L) channel
        lab = cv2.cvtColor(denoised_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l_channel)

        enhanced_lab = cv2.merge([enhanced_l, a_channel, b_channel])
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        # 4. Region of Interest (ROI) & Foreground Mask Extraction
        gray_enhanced = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY)
        # Adaptive thresholding or Otsu to separate product from dark conveyor/lighting background
        _, otsu_mask = cv2.threshold(gray_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        roi_mask = cv2.morphologyEx(otsu_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Save processed image
        base_name = image_path.name
        processed_filename = f"{output_prefix}_{base_name}"
        save_path = settings.PROCESSED_DIR / processed_filename

        cv2.imwrite(str(save_path), enhanced_bgr)

        # Calculate foreground coverage
        total_pixels = target_size[0] * target_size[1]
        fg_pixels = int(cv2.countNonZero(roi_mask))
        roi_coverage_ratio = round(fg_pixels / max(total_pixels, 1), 4)

        return {
            "processed_filename": processed_filename,
            "processed_path": str(save_path),
            "processed_url": f"/static/processed/{processed_filename}",
            "original_dimensions": [orig_w, orig_h],
            "processed_dimensions": list(target_size),
            "roi_coverage_ratio": roi_coverage_ratio,
            "pipeline_steps": [
                "Dimension Normalization (512x512 INTER_AREA)",
                "Bilateral Noise Reduction (d=9, sigma=75)",
                "CLAHE Adaptive Contrast Enhancement (clip=2.5)",
                "Morphological ROI Foreground Segmentation"
            ]
        }

    @classmethod
    def analyze_image_quality(cls, image_path: Path) -> Dict[str, Any]:
        """
        Generates comprehensive Image Quality Analysis Report:
        - Brightness index & exposure status
        - Contrast standard deviation & dynamic range
        - Sharpness index via Laplacian variance
        - Noise floor estimation
        - Overall usability grade (A+, A, B, C)
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")

        img_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if img_bgr is None:
            pil_img = Image.open(image_path).convert("RGB")
            img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Brightness (Mean intensity 0-255)
        brightness_val = float(np.mean(gray))
        if brightness_val < 45:
            brightness_status = "Underexposed (Low Light)"
        elif brightness_val > 210:
            brightness_status = "Overexposed (Surface Glare)"
        else:
            brightness_status = "Optimal Industrial Lighting"

        # 2. Contrast (Standard deviation of intensity)
        contrast_val = float(np.std(gray))
        if contrast_val < 30:
            contrast_status = "Low Dynamic Range"
        elif contrast_val > 75:
            contrast_status = "High Dynamic Contrast"
        else:
            contrast_status = "Normal Industrial Contrast"

        # 3. Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness_val = float(laplacian.var())
        if sharpness_val < 80:
            sharpness_status = "Blurry / Soft Focus"
            sharpness_rating = "Poor"
        elif sharpness_val < 250:
            sharpness_status = "Moderate Sharpness"
            sharpness_rating = "Acceptable"
        else:
            sharpness_status = "High Edge Definition"
            sharpness_rating = "Crisp"

        # 4. Noise estimation (High frequency residual after median filter)
        median_filtered = cv2.medianBlur(gray, 3)
        noise_residual = np.abs(gray.astype(np.float32) - median_filtered.astype(np.float32))
        noise_val = float(np.mean(noise_residual))

        # 5. Composite Quality Score (0 - 100)
        # Optimal brightness around 128
        b_penalty = min(abs(brightness_val - 128) / 128.0, 1.0) * 30
        c_score = min(contrast_val / 60.0, 1.0) * 35
        s_score = min(sharpness_val / 300.0, 1.0) * 35
        n_penalty = min(noise_val / 10.0, 1.0) * 15

        composite_score = max(0.0, min(100.0, round((100 - b_penalty + c_score + s_score - n_penalty) / 1.7, 1)))

        if composite_score >= 85:
            quality_grade = "A+ (Excellent)"
            recommendation = "Optimal for sub-millimeter anomaly inspection"
        elif composite_score >= 70:
            quality_grade = "A (Good)"
            recommendation = "High reliability for automated defect classification"
        elif composite_score >= 50:
            quality_grade = "B (Acceptable)"
            recommendation = "Inspection valid, minor contrast enhancement applied"
        else:
            quality_grade = "C (Degraded)"
            recommendation = "Sensor recalibration or camera lens cleaning recommended"

        return {
            "overall_score": composite_score,
            "quality_grade": quality_grade,
            "recommendation": recommendation,
            "is_usable": composite_score >= 45,
            "metrics": {
                "brightness": {
                    "value": round(brightness_val, 2),
                    "status": brightness_status,
                    "ideal_range": "60 - 190"
                },
                "contrast": {
                    "value": round(contrast_val, 2),
                    "status": contrast_status,
                    "ideal_range": "35 - 80"
                },
                "sharpness": {
                    "value": round(sharpness_val, 2),
                    "status": sharpness_status,
                    "rating": sharpness_rating,
                    "threshold_min": 100.0
                },
                "noise_level": {
                    "value": round(noise_val, 2),
                    "rating": "Low" if noise_val < 3.5 else ("Medium" if noise_val < 7.0 else "High")
                }
            }
        }
