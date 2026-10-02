import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from preprocessing.preprocess import preprocess_image

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    "bottle", "cable", "capsule", "carpet", "grid",
    "hazelnut", "leather", "metal_nut", "pill", "screw",
    "tile", "toothbrush", "transistor", "wood", "zipper"
]

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 50
LEARNING_RATE = 0.0005


class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 3, 2, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, 2, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 3, 2, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True)
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 3, 2, 1, output_padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 64, 3, 2, 1, output_padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, 3, 2, 1, output_padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 3, 3, 2, 1, output_padding=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


class CombinedLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.mse = nn.MSELoss()
        self.l1 = nn.L1Loss()

    def forward(self, output, target):
        return 0.7 * self.mse(output, target) + 0.3 * self.l1(output, target)


def load_good_images(category):
    good_dir = DATASET_DIR / category / "train" / "good"

    if not good_dir.exists():
        print(f"ERROR: Folder not found: {good_dir}")
        return None

    image_files = sorted(good_dir.glob("*.png"))

    if not image_files:
        print(f"ERROR: No PNG images found for {category}")
        return None

    images = []
    skipped = 0

    for image_file in image_files:
        try:
            normalized, _ = preprocess_image(image_file)

            if normalized.shape != (IMAGE_SIZE[1], IMAGE_SIZE[0], 3):
                raise ValueError(
                    f"Unexpected preprocessed shape: {normalized.shape}"
                )

            images.append(normalized)

        except Exception as error:
            skipped += 1
            print(f"WARNING: Skipping {image_file.name}: {error}")

    if not images:
        print(f"ERROR: Could not preprocess images for {category}")
        return None

    images = np.asarray(images, dtype=np.float32)
    images = np.transpose(images, (0, 3, 1, 2))

    tensor = torch.from_numpy(images).float()

    print(f"Successfully preprocessed: {len(tensor)} images")

    if skipped:
        print(f"Skipped images: {skipped}")

    return tensor


def train_category(category, device):
    print()
    print("=" * 70)
    print(f"TRAINING PREPROCESSED AUTOENCODER: {category.upper()}")
    print("=" * 70)

    data = load_good_images(category)

    if data is None:
        print(f"Skipping {category}")
        return False

    print(f"Training images found: {len(data)}")
    print(f"Input shape: {tuple(data.shape)}")

    dataset = TensorDataset(data, data)

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        pin_memory=torch.cuda.is_available()
    )

    model = ConvAutoencoder().to(device)
    criterion = CombinedLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-5
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=5,
        min_lr=1e-6
    )

    best_loss = float("inf")
    best_state = None
    model.train()

    for epoch in range(EPOCHS):
        total_loss = 0.0

        for images, targets in loader:
            images = images.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            outputs = model(images)
            loss = criterion(outputs, targets)

            loss.backward()

            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=1.0
            )

            optimizer.step()
            total_loss += loss.item()

        average_loss = total_loss / len(loader)
        scheduler.step(average_loss)

        current_lr = optimizer.param_groups[0]["lr"]

        print(
            f"Epoch [{epoch + 1:02d}/{EPOCHS}] "
            f"Loss: {average_loss:.6f} "
            f"LR: {current_lr:.7f}"
        )

        if average_loss < best_loss:
            best_loss = average_loss
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

    if best_state is not None:
        model.load_state_dict(best_state)

    model_path = MODEL_DIR / f"{category}_autoencoder.pth"

    torch.save(model.state_dict(), model_path)

    print(f"Best training loss: {best_loss:.6f}")
    print(f"Model saved at: {model_path}")

    return True


def main():
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("PREPROCESSED AUTOENCODER TRAINING - ALL 15 MVTec CATEGORIES")
    print("=" * 70)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Device: {device}")
    print(f"Preprocessing input: {IMAGE_SIZE[0]} x {IMAGE_SIZE[1]}")
    print(
        "Preprocessing: resize + bilateral denoising + "
        "CLAHE + normalization"
    )

    successful = 0

    for category in CATEGORIES:
        if train_category(category, device):
            successful += 1

    print()
    print("=" * 70)
    print("ALL 15 AUTOENCODER TRAINING COMPLETED")
    print("=" * 70)
    print(f"Models trained successfully: {successful}/{len(CATEGORIES)}")

    print()
    print("Saved models:")

    for category in CATEGORIES:
        model_path = MODEL_DIR / f"{category}_autoencoder.pth"

        if model_path.exists():
            print(f"[OK] {model_path.name}")
        else:
            print(f"[MISSING] {model_path.name}")


if __name__ == "__main__":
    main()
