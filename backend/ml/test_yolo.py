from pathlib import Path

from ultralytics import YOLO




PROJECT_ROOT = Path(__file__).resolve().parents[2]



MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "best (2).pt"
)


print("YOLO model path:")
print(MODEL_PATH)

print("Model exists:", MODEL_PATH.exists())



print()
print("Loading YOLO26n model...")

model = YOLO(
    str(MODEL_PATH)
)

print("YOLO26n loaded successfully!")



DATASET_PATH = PROJECT_ROOT / "dataset1"

print()
print("Searching for test images in:")
print(DATASET_PATH)


image_files = []

for extension in ["*.png", "*.jpg", "*.jpeg", "*.bmp"]:

    image_files.extend(
        DATASET_PATH.glob(
            f"**/test/**/{extension}"
        )
    )


image_files = sorted(set(image_files))


if not image_files:

    raise FileNotFoundError(
        f"No test images found inside:\n{DATASET_PATH}"
    )


print("Test images found:", len(image_files))


# Use the same type of image that we just tested
image_path = image_files[0]

print()
print("Testing image:")
print(image_path)




print()
print("Running YOLO prediction...")

results = model.predict(
    source=str(image_path),
    conf=0.25,
    verbose=False
)




result = results[0]

print()
print("=" * 55)
print("             YOLO DETECTION RESULT")
print("=" * 55)




if result.boxes is None or len(result.boxes) == 0:

    print("No defect detected.")

else:

    print(
        "Defects detected:",
        len(result.boxes)
    )

    print()

    for i, box in enumerate(result.boxes):

        # Bounding box coordinates
        x1, y1, x2, y2 = (
            box.xyxy[0]
            .cpu()
            .numpy()
        )

        # YOLO confidence
        confidence = (
            box.conf[0]
            .cpu()
            .item()
        )

        # Class ID
        class_id = (
            box.cls[0]
            .cpu()
            .item()
        )

        print(
            f"Detection {i + 1}"
        )

        print(
            "Class ID   :",
            int(class_id)
        )

        print(
            "Confidence :",
            round(confidence * 100, 2),
            "%"
        )

        print(
            "Bounding box:",
            [
                round(float(x1), 2),
                round(float(y1), 2),
                round(float(x2), 2),
                round(float(y2), 2)
            ]
        )

        print("-" * 40)


print("=" * 55)