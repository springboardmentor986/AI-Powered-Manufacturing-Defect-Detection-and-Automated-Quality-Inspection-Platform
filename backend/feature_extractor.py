import timm
import torch


# ==========================================
# Load Pretrained ResNet18
# ==========================================

model = timm.create_model(
    "resnet18",
    pretrained=True,
    num_classes=0
)

model.eval()


# ==========================================
# ImageNet Normalization Values
# ==========================================

MEAN = torch.tensor(
    [0.485, 0.456, 0.406]
).view(1, 3, 1, 1)

STD = torch.tensor(
    [0.229, 0.224, 0.225]
).view(1, 3, 1, 1)


# ==========================================
# Feature Extraction
# ==========================================

def extract_features(image):

    # Convert NumPy image to PyTorch tensor
    tensor = torch.tensor(
        image,
        dtype=torch.float32
    )

    # Change:
    # Height, Width, Channels
    # to:
    # Channels, Height, Width

    tensor = tensor.permute(
        2, 0, 1
    )

    # Add batch dimension

    tensor = tensor.unsqueeze(0)

    # Apply ImageNet normalization

    tensor = (
        tensor - MEAN
    ) / STD

    # Extract ResNet18 features

    with torch.no_grad():

        features = model(tensor)

    return features


print("Feature extractor ready")