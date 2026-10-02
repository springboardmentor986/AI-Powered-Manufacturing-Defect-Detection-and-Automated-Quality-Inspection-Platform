import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
import torch.nn as nn
import torch.optim as optim

from models.autoencoder import ConvAutoencoder


# --------------------------------------------------
# Configuration
# --------------------------------------------------

IMAGE_SIZE = (224, 224)

DATASET_DIR = r"D:\VisionInspectAI\ml\dataset\bottle\train\good"

MODEL_DIR = r"D:\VisionInspectAI\ml\saved_models"

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "bottle_autoencoder_improved.pth"
)

BATCH_SIZE = 16
EPOCHS = 30
LEARNING_RATE = 0.0005


# --------------------------------------------------
# Load images
# --------------------------------------------------

images = []

print("Loading training images...")

for filename in os.listdir(DATASET_DIR):

    if filename.lower().endswith((".png", ".jpg", ".jpeg")):

        image_path = os.path.join(DATASET_DIR, filename)

        image = cv2.imread(image_path)

        if image is None:
            continue

        # Resize
        image = cv2.resize(image, IMAGE_SIZE)

        # BGR → RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Normalize
        image = image.astype(np.float32) / 255.0

        images.append(image)


images = np.array(images, dtype=np.float32)

print("Found", len(images), "training images.")
print("NumPy shape:", images.shape)


# --------------------------------------------------
# Convert to PyTorch format
# --------------------------------------------------

images_tensor = torch.tensor(images)

# (N, H, W, C) → (N, C, H, W)
images_tensor = images_tensor.permute(0, 3, 1, 2)

print("PyTorch shape:", images_tensor.shape)


# Autoencoder target = input itself
dataset = TensorDataset(images_tensor, images_tensor)

dataloader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)


# --------------------------------------------------
# Device
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)


# --------------------------------------------------
# Create model
# --------------------------------------------------

model = ConvAutoencoder().to(device)

criterion = nn.MSELoss()

optimizer = optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-5
)


# --------------------------------------------------
# Training
# --------------------------------------------------

print("\nStarting improved model training...\n")

for epoch in range(EPOCHS):

    model.train()

    running_loss = 0.0

    for batch_images, targets in dataloader:

        batch_images = batch_images.to(device)
        targets = targets.to(device)

        # Forward pass
        outputs = model(batch_images)

        # Reconstruction loss
        loss = criterion(outputs, targets)

        # Backpropagation
        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

    epoch_loss = running_loss / len(dataloader)

    print(
        f"Epoch [{epoch + 1}/{EPOCHS}] "
        f"Loss: {epoch_loss:.6f}"
    )


# --------------------------------------------------
# Save model
# --------------------------------------------------

os.makedirs(MODEL_DIR, exist_ok=True)

torch.save(model.state_dict(), MODEL_PATH)

print("\n" + "=" * 50)
print("IMPROVED MODEL TRAINING COMPLETED!")
print("=" * 50)

print("Model saved at:")
print(MODEL_PATH)