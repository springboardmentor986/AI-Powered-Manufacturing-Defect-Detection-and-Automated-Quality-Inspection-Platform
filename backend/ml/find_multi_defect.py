from pathlib import Path
from ultralytics import YOLO

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# YOLO model
MODEL_PATH = PROJECT_ROOT / "models" / "best (2).pt"

# Dataset
DATASET_PATH = PROJECT_ROOT / "dataset1"

# Load model
print("Loading YOLO...")
model = YOLO(str(MODEL_PATH))
print("YOLO loaded!")

# Find all test images
image_files = []

for ext in ["*.png", "*.jpg", "*.jpeg", "*.bmp"]:
    image_files.extend(DATASET_PATH.glob(f"**/test/**/{ext}"))

print(f"Test images found: {len(image_files)}")

print("\nSearching for images with multiple detections...\n")

found = 0

for image_path in image_files:

    results = model(
        str(image_path),
        verbose=False
    )

    result = results[0]

    number_of_boxes = len(result.boxes)

    if number_of_boxes >= 2:

        print("=" * 60)
        print("MULTIPLE DETECTIONS FOUND")
        print("=" * 60)

        print(f"Image: {image_path}")
        print(f"Detections: {number_of_boxes}")

        for i, box in enumerate(result.boxes, start=1):

            confidence = float(box.conf[0])

            coordinates = box.xyxy[0].tolist()

            print(f"\nDetection {i}")
            print(f"Confidence: {confidence * 100:.2f}%")
            print(f"Bounding box: {coordinates}")

        found += 1

        
        if found == 5:
            break


if found == 0:
    print("No image with multiple detections was found.")
else:
    print("\nSearch complete.")
    print(f"Found {found} images with multiple detections.")