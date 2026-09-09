from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import AdamW

from ai.models.defect_segmenter import UNet
from ai.evaluation.create_segmentation_loaders import (
    create_dataloaders,
)


# ============================================================
# Configuration
# ============================================================

EPOCHS = 20

LEARNING_RATE = 1e-4

WEIGHT_DECAY = 1e-4

MODEL_DIRECTORY = Path("ai/models")

MODEL_PATH = (
    MODEL_DIRECTORY
    / "defect_segmenter_unet.pt"
)


# ============================================================
# Device
# ============================================================

def get_device():

    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


# ============================================================
# Dice Loss
# ============================================================

class DiceLoss(nn.Module):

    def __init__(self, smooth=1.0):
        super().__init__()

        self.smooth = smooth

    def forward(self, logits, targets):

        probabilities = torch.sigmoid(logits)

        probabilities = probabilities.reshape(
            probabilities.size(0),
            -1,
        )

        targets = targets.reshape(
            targets.size(0),
            -1,
        )

        intersection = (
            probabilities * targets
        ).sum(dim=1)

        dice = (
            2.0 * intersection
            + self.smooth
        ) / (
            probabilities.sum(dim=1)
            + targets.sum(dim=1)
            + self.smooth
        )

        return (1.0 - dice).mean()


# ============================================================
# Combined Loss
# ============================================================

class BCEDiceLoss(nn.Module):

    def __init__(self):

        super().__init__()

        self.bce = nn.BCEWithLogitsLoss()

        self.dice = DiceLoss()

    def forward(self, logits, targets):

        bce_loss = self.bce(
            logits,
            targets,
        )

        dice_loss = self.dice(
            logits,
            targets,
        )

        return bce_loss + dice_loss


# ============================================================
# Training
# ============================================================

def train_one_epoch(
    model,
    loader,
    optimizer,
    criterion,
    device,
):

    model.train()

    total_loss = 0.0

    for images, masks in loader:

        images = images.to(device)

        masks = masks.to(device)

        # Clear previous gradients
        optimizer.zero_grad()

        # Forward pass
        logits = model(images)

        # Calculate loss
        loss = criterion(
            logits,
            masks,
        )

        # Backpropagation
        loss.backward()

        # Update model parameters
        optimizer.step()

        total_loss += (
            loss.item()
            * images.size(0)
        )

    average_loss = (
        total_loss
        / len(loader.dataset)
    )

    return average_loss


# ============================================================
# Validation
# ============================================================

def validate(
    model,
    loader,
    criterion,
    device,
):

    model.eval()

    total_loss = 0.0

    with torch.no_grad():

        for images, masks in loader:

            images = images.to(device)

            masks = masks.to(device)

            logits = model(images)

            loss = criterion(
                logits,
                masks,
            )

            total_loss += (
                loss.item()
                * images.size(0)
            )

    average_loss = (
        total_loss
        / len(loader.dataset)
    )

    return average_loss


# ============================================================
# Main
# ============================================================

def main():

    print("U-Net Defect Segmentation Training")

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = get_device()

    print(
        f"\nUsing device: {device}"
    )

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    (
        train_loader,
        validation_loader,
        test_loader,
    ) = create_dataloaders()

    print(
        f"Training samples: "
        f"{len(train_loader.dataset)}"
    )

    print(
        f"Validation samples: "
        f"{len(validation_loader.dataset)}"
    )

    print(
        f"Test samples: "
        f"{len(test_loader.dataset)}"
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = UNet(
        in_channels=3,
        out_channels=1,
    ).to(device)

    # --------------------------------------------------------
    # Loss
    # --------------------------------------------------------

    criterion = BCEDiceLoss()

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    best_validation_loss = float("inf")

    MODEL_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    for epoch in range(1, EPOCHS + 1):

        train_loss = train_one_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            device=device,
        )

        validation_loss = validate(
            model=model,
            loader=validation_loader,
            criterion=criterion,
            device=device,
        )

        print(
            f"Epoch {epoch:02d}/{EPOCHS} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Validation Loss: {validation_loss:.4f}"
        )

        # ----------------------------------------------------
        # Save best model
        # ----------------------------------------------------

        if validation_loss < best_validation_loss:

            best_validation_loss = validation_loss

            torch.save(
                model.state_dict(),
                MODEL_PATH,
            )

            print(
                f"  [INFO] Saved best model "
                f"-> {MODEL_PATH}"
            )


    print(
        "Training complete."
    )

    print(
        f"Best validation loss: "
        f"{best_validation_loss:.4f}"
    )

    print(
        f"Model saved at: "
        f"{MODEL_PATH}"
    )


if __name__ == "__main__":
    main()