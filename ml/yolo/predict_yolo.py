from ultralytics import YOLO
from pathlib import Path

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "runs" / "bottle_defect_improved" / "weights" / "best.pt"
TEST_IMAGES = BASE_DIR / "dataset" / "test" / "images"

# --------------------------------------------------
# Load trained YOLO model
# --------------------------------------------------

print("=" * 60)
print("Loading improved YOLO model")
print("=" * 60)

model = YOLO(str(MODEL_PATH))

print("Improved YOLO model loaded successfully!")

# --------------------------------------------------
# Run prediction on test images
# --------------------------------------------------

print("\n" + "=" * 60)
print("Running YOLO predictions on TEST images")
print("=" * 60)

results = model.predict(
    source=str(TEST_IMAGES),
    imgsz=640,
    conf=0.25,
    save=True,
    save_txt=True,
    save_conf=True
)

print("\n" + "=" * 60)
print("PREDICTION COMPLETED")
print("=" * 60)

print("Number of images processed:", len(results))

print("\nPredicted images are saved in:")
print(Path("runs/detect").resolve())

print("=" * 60)