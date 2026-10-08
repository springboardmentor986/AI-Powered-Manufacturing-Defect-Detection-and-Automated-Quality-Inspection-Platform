"""
Milestone 4 — trains a convolutional autoencoder per category, upgrading
the Milestone 2 statistical baseline to a genuinely trained model, as
discussed with the mentor.

Requires PyTorch (CPU build is fine, no GPU needed for this dataset
size):
    pip install torch --index-url https://download.pytorch.org/whl/cpu

Usage (from the backend project root, with venv active):
    python train_autoencoder.py                       # trains all categories
    python train_autoencoder.py --category bottle      # just one category
    python train_autoencoder.py --epochs 30            # more training
"""

import argparse
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from app.vision.autoencoder import ConvAutoencoder
from app.vision.preprocessing import preprocess_path

DATASET_IMAGES_DIR = Path("dataset_images")
ARTIFACTS_DIR = Path("model_artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)


def load_training_tensor(category_dir: Path) -> torch.Tensor:
    good_dir = category_dir / "train" / "good"
    paths = sorted(good_dir.glob("*.png"))
    images = [preprocess_path(str(p)) for p in paths]
    arr = np.stack(images).astype(np.float32)          # (N, 128, 128)
    return torch.from_numpy(arr).unsqueeze(1)            # (N, 1, 128, 128)


def train_one_category(category_name: str, category_dir: Path, epochs: int, batch_size: int = 16):
    tensor = load_training_tensor(category_dir)
    if len(tensor) == 0:
        print(f"  skip {category_name}: no training images")
        return

    loader = DataLoader(TensorDataset(tensor), batch_size=batch_size, shuffle=True)

    model = ConvAutoencoder()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for (batch,) in loader:
            optimizer.zero_grad()
            output = model(batch)
            loss = criterion(output, batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * batch.size(0)
        avg_loss = total_loss / len(tensor)
        if (epoch + 1) % 5 == 0 or epoch == epochs - 1:
            print(f"    epoch {epoch + 1}/{epochs} - loss: {avg_loss:.5f}")

    save_path = ARTIFACTS_DIR / f"{category_name}_autoencoder.pt"
    torch.save(model.state_dict(), save_path)
    print(f"  saved {save_path} ({len(tensor)} training images)")


def main():
    parser = argparse.ArgumentParser(description="Train per-category autoencoders")
    parser.add_argument("--category", help="Train only this category (default: all)")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()

    if not DATASET_IMAGES_DIR.exists():
        print("ERROR: dataset_images/ not found. Run load_mvtec_dataset.py first.")
        return

    categories = sorted([p for p in DATASET_IMAGES_DIR.iterdir() if p.is_dir()])
    if args.category:
        categories = [c for c in categories if c.name == args.category]
        if not categories:
            print(f"ERROR: category '{args.category}' not found.")
            return

    for cat_dir in categories:
        print(f"Training {cat_dir.name}...")
        train_one_category(cat_dir.name, cat_dir, args.epochs)

    print("\nDone. Run evaluate_accuracy.py to check the new accuracy.")


if __name__ == "__main__":
    main()
