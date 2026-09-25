import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path




PROJECT_ROOT = Path(__file__).resolve().parents[2]




MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "defect_classifier_resnet18_final.pth"
)

print("Model path:")
print(MODEL_PATH)

print("Exists:", MODEL_PATH.exists())


device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)



model = models.resnet18(weights=None)

model.fc = nn.Linear(
    model.fc.in_features,
    48
)


checkpoint = torch.load(
    MODEL_PATH,
    map_location=device
)

if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    model.load_state_dict(
        checkpoint["model_state_dict"]
    )
else:
    model.load_state_dict(checkpoint)




model = model.to(device)

model.eval()


print("ResNet18 loaded successfully!")
print("Number of output classes:", 48)