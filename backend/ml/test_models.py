from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

YOLO_MODEL = (
    PROJECT_ROOT
    / "models"
    / "best (2).pt"
)

RESNET_MODEL = (
    PROJECT_ROOT
    / "models"
    / "defect_classifier_resnet18_final.pth"
)

print("YOLO model:")
print(YOLO_MODEL)
print("Exists:", YOLO_MODEL.exists())

print()

print("ResNet18 model:")
print(RESNET_MODEL)
print("Exists:", RESNET_MODEL.exists())