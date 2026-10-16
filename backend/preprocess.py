from PIL import Image
import numpy as np
import cv2
from io import BytesIO

IMAGE_SIZE = (256, 256)


def preprocess_image(image_bytes):
    image = Image.open(BytesIO(image_bytes))
    image = image.convert("RGB")
    image = image.resize(IMAGE_SIZE)

    image_array = np.array(image)
    image_array = image_array / 255.0

    return image_array


def analyze_image_quality(image_bytes):
    image = Image.open(BytesIO(image_bytes))
    image = image.convert("RGB")

    image_array = np.array(image)

    width, height = image.size

    gray = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2GRAY
    )

    brightness = float(np.mean(gray))

    contrast = float(np.std(gray))

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    brightness_ok = 50 <= brightness <= 200
    contrast_ok = contrast >= 20
    sharpness_ok = sharpness >= 100

    if brightness_ok and contrast_ok and sharpness_ok:
        quality_status = "PASS"
    else:
        quality_status = "WARNING"

    return {
        "resolution": {
            "width": width,
            "height": height
        },
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "sharpness": round(sharpness, 2),
        "quality_status": quality_status
    }