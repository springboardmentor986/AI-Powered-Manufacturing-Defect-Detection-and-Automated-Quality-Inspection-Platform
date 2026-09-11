import cv2
import os
import numpy as np
from PIL import Image
import uuid

def advanced_preprocess_image(input_path: str, output_dir: str = "processed") -> dict:
    """
    Advanced image preprocessing for Milestone 2:
    - Read image
    - Resize to 224x224
    - Convert to RGB
    - Noise Removal (Gaussian Blur)
    - Image Enhancement (Histogram Equalization)
    - Normalization
    - Save processed image
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Read image
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError("Could not read image")
    
    height, width = img.shape[:2]
    
    # Convert BGR to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize to 224x224
    resized = cv2.resize(img_rgb, (224, 224), interpolation=cv2.INTER_AREA)
    
    # Step 1: Noise Removal using Gaussian Blur
    denoised = cv2.GaussianBlur(resized, (5, 5), 0)
    
    # Step 2: Image Enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    lab = cv2.cvtColor(denoised, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    # Step 3: Normalization to [0, 1]
    normalized = enhanced.astype(np.float32) / 255.0
    
    # Save processed image
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    processed_filename = f"{name}_processed_{uuid.uuid4().hex[:8]}.jpg"
    processed_path = os.path.join(output_dir, processed_filename)
    
    img_to_save = (normalized * 255).astype(np.uint8)
    Image.fromarray(img_to_save).save(processed_path)
    
    return {
        "processed_path": processed_path,
        "original_width": width,
        "original_height": height,
        "processed_width": 224,
        "processed_height": 224,
        "file_size": os.path.getsize(input_path),
        "steps": [
            "Resize to 224x224",
            "Noise Removal (Gaussian Blur)",
            "Image Enhancement (CLAHE)",
            "Normalization"
        ]
    }
