from pathlib import Path
from PIL import Image
import numpy as np

DATASET_PATH = Path("dataset/mvtec_ad/bottle")
TRAIN_PATH = DATASET_PATH / "train" / "good"

IMAGE_SIZE = (128, 128)


def load_training_images():
    images = []

    for image_path in sorted(TRAIN_PATH.glob("*.png")):
        image = Image.open(image_path).convert("RGB")
        image = image.resize(IMAGE_SIZE)

        image_array = np.asarray(image, dtype=np.float32) / 255.0
        images.append(image_array)

    return np.array(images)


if __name__ == "__main__":
    print("=" * 55)
    print("VisionInspect AI - Image Preprocessing")
    print("=" * 55)

    images = load_training_images()

    print(f"Training images loaded : {len(images)}")
    print(f"Image size             : {IMAGE_SIZE}")
    print(f"Array shape             : {images.shape}")
    print(f"Pixel range             : {images.min():.3f} - {images.max():.3f}")

    print("=" * 55)
    print("Preprocessing completed successfully.")
    print("=" * 55)