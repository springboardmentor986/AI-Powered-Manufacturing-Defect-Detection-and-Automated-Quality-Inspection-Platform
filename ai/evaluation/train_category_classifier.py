import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from ai.models.category_classifier import CategoryClassifier, get_default_device

CACHE_DIR = Path("ai/models/features_cache")


def train_category_classifier_from_features(
    epochs=15,
    batch_size=64,
    lr=1e-3,
    save_path="ai/models/category_classifier_resnet18.pt",
):
    device = get_default_device()
    print(f"Training Category Classifier on device: {device}", flush=True)

    train_data = torch.load(CACHE_DIR / "train_features.pt", weights_only=True)
    val_data = torch.load(CACHE_DIR / "val_features.pt", weights_only=True)

    X_train, y_train = train_data["features"], train_data["cat_indices"]
    X_val, y_val = val_data["features"], val_data["cat_indices"]

    print(f"Loaded {len(X_train)} train features and {len(X_val)} val features.", flush=True)

    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=batch_size, shuffle=False)

    head = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(512, 15),
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    best_head_state = None

    for epoch in range(1, epochs + 1):
        start_t = time.time()
        head.train()
        train_loss = 0.0
        train_correct = 0

        for feats, labels in train_loader:
            feats, labels = feats.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = head(feats)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * feats.size(0)
            preds = torch.argmax(outputs, dim=1)
            train_correct += (preds == labels).sum().item()

        scheduler.step()

        # Validation
        head.eval()
        val_loss = 0.0
        val_correct = 0
        with torch.no_grad():
            for feats, labels in val_loader:
                feats, labels = feats.to(device), labels.to(device)
                outputs = head(feats)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * feats.size(0)
                preds = torch.argmax(outputs, dim=1)
                val_correct += (preds == labels).sum().item()

        train_acc = train_correct / len(X_train)
        val_acc = val_correct / len(X_val)
        elapsed = time.time() - start_t

        print(
            f"Epoch {epoch:02d}/{epochs} ({elapsed:.2f}s) | "
            f"Train Loss: {train_loss / len(X_train):.4f}, Train Acc: {train_acc * 100:.2f}% | "
            f"Val Loss: {val_loss / len(X_val):.4f}, Val Acc: {val_acc * 100:.2f}%",
            flush=True,
        )

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_head_state = {k: v.cpu() for k, v in head.state_dict().items()}

    # Assemble full ResNet18 CategoryClassifier
    full_model = CategoryClassifier(num_classes=15, pretrained=True)
    full_model.backbone.fc.load_state_dict(best_head_state)

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(full_model.state_dict(), save_path)
    print(f"\nSaved full Category Classifier checkpoint (Val Acc: {best_val_acc * 100:.2f}%) to {save_path}", flush=True)


if __name__ == "__main__":
    train_category_classifier_from_features()
