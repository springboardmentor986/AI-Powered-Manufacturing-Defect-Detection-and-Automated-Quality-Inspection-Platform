import json
from pathlib import Path
from typing import Dict, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from ai.models.category_classifier import get_default_device
from ai.models.defect_classifier import (
    GlobalDefectClassifier,
    HierarchicalDefectClassifier,
)

CACHE_DIR = Path("ai/models/features_cache")


def train_hierarchical_defect_classifier(
    epochs=20,
    batch_size=32,
    lr=1e-3,
    save_path="ai/models/defect_classifier_hierarchical.pt",
):
    device = get_default_device()
    print(f"\n========================================================", flush=True)
    print(f"Training Hierarchical Defect Classifier (Option B) on {device}", flush=True)
    print(f"========================================================", flush=True)

    with open("ai/models/defect_classes.json", "r", encoding="utf-8") as f:
        defect_classes: Dict[str, List[str]] = json.load(f)

    train_data = torch.load(CACHE_DIR / "train_features.pt", weights_only=True)
    val_data = torch.load(CACHE_DIR / "val_features.pt", weights_only=True)

    # Initialize full model
    model = HierarchicalDefectClassifier(defect_classes_dict=defect_classes, pretrained=True)

    total_val_correct = 0
    total_val_samples = 0

    # Train each category-specific head
    for cat, def_list in sorted(defect_classes.items()):
        # Filter samples for this category
        train_mask = [c == cat for c in train_data["categories"]]
        val_mask = [c == cat for c in val_data["categories"]]

        X_tr = train_data["features"][train_mask]
        y_tr = train_data["local_indices"][train_mask]

        X_v = val_data["features"][val_mask]
        y_v = val_data["local_indices"][val_mask]

        num_classes = len(def_list)
        head = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(512, num_classes),
        ).to(device)

        # Compute balanced class weights to handle heavy imbalance ('good' vs rare defects)
        counts = torch.bincount(y_tr, minlength=num_classes).float()
        weights = 1.0 / (counts + 1.0)
        weights = weights / weights.sum() * num_classes

        criterion = nn.CrossEntropyLoss(weight=weights.to(device))
        optimizer = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        tr_loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=min(batch_size, len(X_tr)), shuffle=True)
        v_loader = DataLoader(TensorDataset(X_v, y_v), batch_size=min(batch_size, len(X_v)), shuffle=False)

        best_head_state = None
        best_v_acc = 0.0

        for ep in range(1, epochs + 1):
            head.train()
            for feats, labels in tr_loader:
                feats, labels = feats.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = head(feats)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

            scheduler.step()

            # Validation
            head.eval()
            v_corr = 0
            with torch.no_grad():
                for feats, labels in v_loader:
                    feats, labels = feats.to(device), labels.to(device)
                    outputs = head(feats)
                    preds = torch.argmax(outputs, dim=1)
                    v_corr += (preds == labels).sum().item()

            v_acc = v_corr / max(len(X_v), 1)
            if v_acc >= best_v_acc:
                best_v_acc = v_acc
                best_head_state = {k: v.cpu() for k, v in head.state_dict().items()}

        model.heads[cat].load_state_dict(best_head_state)
        v_corr_final = int(best_v_acc * len(X_v))
        total_val_correct += v_corr_final
        total_val_samples += len(X_v)
        print(f"  [{cat:12s}] Classes: {num_classes:2d} | Train: {len(X_tr):3d} | Val: {len(X_v):2d} | Best Val Acc: {best_v_acc * 100:.1f}%", flush=True)

    overall_val_acc = total_val_correct / total_val_samples
    print(f"\nOption B Hierarchical Overall Val Acc: {overall_val_acc * 100:.2f}%", flush=True)

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"Saved best Hierarchical Defect Classifier to {save_path}", flush=True)
    return overall_val_acc


def train_global_defect_classifier_baseline(
    epochs=15,
    batch_size=64,
    lr=1e-3,
    save_path="ai/models/defect_classifier_global_baseline.pt",
):
    device = get_default_device()
    print(f"\n========================================================", flush=True)
    print(f"Training Monolithic Global Flat Classifier (Option A Baseline) on {device}", flush=True)
    print(f"========================================================", flush=True)

    with open("ai/models/defect_global_classes.json", "r", encoding="utf-8") as f:
        global_classes = json.load(f)

    num_classes = len(global_classes)
    print(f"Option A Total Global Classes across all categories: {num_classes}", flush=True)

    train_data = torch.load(CACHE_DIR / "train_features.pt", weights_only=True)
    val_data = torch.load(CACHE_DIR / "val_features.pt", weights_only=True)

    X_tr, y_tr = train_data["features"], train_data["global_indices"]
    X_v, y_v = val_data["features"], val_data["global_indices"]

    head = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(512, num_classes),
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    tr_loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=batch_size, shuffle=True)
    v_loader = DataLoader(TensorDataset(X_v, y_v), batch_size=batch_size, shuffle=False)

    best_v_acc = 0.0
    best_head_state = None

    for ep in range(1, epochs + 1):
        head.train()
        for feats, labels in tr_loader:
            feats, labels = feats.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = head(feats)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        scheduler.step()

        # Validation
        head.eval()
        v_corr = 0
        with torch.no_grad():
            for feats, labels in v_loader:
                feats, labels = feats.to(device), labels.to(device)
                outputs = head(feats)
                preds = torch.argmax(outputs, dim=1)
                v_corr += (preds == labels).sum().item()

        v_acc = v_corr / len(X_v)
        if v_acc >= best_v_acc:
            best_v_acc = v_acc
            best_head_state = {k: v.cpu() for k, v in head.state_dict().items()}

        if ep % 5 == 0 or ep == epochs:
            print(f"  Option A Epoch {ep:02d}/{epochs} | Val Acc: {v_acc * 100:.2f}%", flush=True)

    print(f"\nOption A Global Baseline Overall Val Acc: {best_v_acc * 100:.2f}%", flush=True)

    # Assemble full Global model
    full_model = GlobalDefectClassifier(num_classes=num_classes, pretrained=True)
    full_model.backbone.fc.load_state_dict(best_head_state)

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(full_model.state_dict(), save_path)
    print(f"Saved Global Baseline Classifier to {save_path}", flush=True)
    return best_v_acc


if __name__ == "__main__":
    train_hierarchical_defect_classifier()
    train_global_defect_classifier_baseline()
