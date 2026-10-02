import os
import copy
import json

import torch
import torch.nn as nn
from torchvision import models, transforms, datasets
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score


# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\VisionInspectAI\ml"

DATASET_DIR = os.path.join(
    BASE_DIR,
    "classification",
    "dataset"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "classification",
    "saved_models"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("IMPROVED CLASSIFIER TRAINING")
print("=" * 70)
print("Device:", device)
print()


# ============================================================
# CATEGORIES TO IMPROVE
# ============================================================

categories = [
    "cable",
    "capsule",
    "pill",
    "screw",
    "transistor",
    "wood",
    "zipper"
]


# ============================================================
# TRAINING SETTINGS
# ============================================================

IMAGE_SIZE = 224
BATCH_SIZE = 16

HEAD_EPOCHS = 5
FINETUNE_EPOCHS = 25

HEAD_LR = 0.0005
FINETUNE_LR = 0.00005

WEIGHT_DECAY = 0.0001

PATIENCE = 7


# ============================================================
# DATA AUGMENTATION
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.RandomHorizontalFlip(p=0.5),

    transforms.RandomRotation(15),

    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# CREATE RESNET18
# ============================================================

def create_model(num_classes):

    model = models.resnet18(
        weights=models.ResNet18_Weights.DEFAULT
    )

    # Freeze everything initially
    for param in model.parameters():
        param.requires_grad = False

    # Replace classifier
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(
            model.fc.in_features,
            num_classes
        )
    )

    # FC must be trainable
    for param in model.fc.parameters():
        param.requires_grad = True

    return model


# ============================================================
# CLASS WEIGHTS
# ============================================================

def calculate_class_weights(dataset):

    counts = [0] * len(dataset.classes)

    for _, label in dataset.samples:
        counts[label] += 1

    total = sum(counts)

    weights = []

    for count in counts:

        if count == 0:
            weights.append(0.0)
        else:
            weights.append(
                total / (len(counts) * count)
            )

    return torch.tensor(
        weights,
        dtype=torch.float32
    )


# ============================================================
# VALIDATION
# ============================================================

def validate(model, loader):

    model.eval()

    all_labels = []
    all_predictions = []

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)

            outputs = model(images)

            predictions = torch.argmax(
                outputs,
                dim=1
            )

            all_labels.extend(
                labels.numpy()
            )

            all_predictions.extend(
                predictions.cpu().numpy()
            )

    accuracy = sum(
        p == y
        for p, y in zip(
            all_predictions,
            all_labels
        )
    ) / len(all_labels)

    f1 = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    return accuracy, f1


# ============================================================
# TRAIN ONE CATEGORY
# ============================================================

def train_category(category):

    print()
    print("=" * 70)
    print("CATEGORY:", category)
    print("=" * 70)

    train_dir = os.path.join(
        DATASET_DIR,
        category,
        "train"
    )

    val_dir = os.path.join(
        DATASET_DIR,
        category,
        "val"
    )

    if not os.path.exists(train_dir):
        print("Training directory not found.")
        return

    if not os.path.exists(val_dir):
        print("Validation directory not found.")
        return

    # --------------------------------------------------------
    # DATASETS
    # --------------------------------------------------------

    train_dataset = datasets.ImageFolder(
        train_dir,
        transform=train_transform
    )

    val_dataset = datasets.ImageFolder(
        val_dir,
        transform=val_transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    class_names = train_dataset.classes

    print("Classes:", class_names)
    print("Training images:", len(train_dataset))
    print("Validation images:", len(val_dataset))

    # --------------------------------------------------------
    # CLASS WEIGHTS
    # --------------------------------------------------------

    class_weights = calculate_class_weights(
        train_dataset
    ).to(device)

    print("Class weights:", class_weights.cpu().numpy())

    criterion = nn.CrossEntropyLoss(
        weight=class_weights
    )

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = create_model(
        len(class_names)
    )

    model = model.to(device)

    # --------------------------------------------------------
    # PHASE 1:
    # TRAIN CLASSIFIER HEAD
    # --------------------------------------------------------

    print()
    print("PHASE 1: Training classifier head")

    optimizer = torch.optim.AdamW(
        model.fc.parameters(),
        lr=HEAD_LR,
        weight_decay=WEIGHT_DECAY
    )

    best_f1 = -1
    best_state = None

    for epoch in range(HEAD_EPOCHS):

        model.train()

        running_loss = 0.0

        for images, labels in train_loader:

            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

        val_accuracy, val_f1 = validate(
            model,
            val_loader
        )

        print(
            f"Head Epoch {epoch + 1}/{HEAD_EPOCHS} | "
            f"Loss: {running_loss / len(train_loader):.4f} | "
            f"Val Accuracy: {val_accuracy:.4f} | "
            f"Val F1: {val_f1:.4f}"
        )

        if val_f1 > best_f1:

            best_f1 = val_f1
            best_state = copy.deepcopy(
                model.state_dict()
            )

    # --------------------------------------------------------
    # LOAD BEST HEAD
    # --------------------------------------------------------

    if best_state is not None:

        model.load_state_dict(
            best_state
        )

    # --------------------------------------------------------
    # PHASE 2:
    # FINE-TUNE LAST RESNET BLOCK + FC
    # --------------------------------------------------------

    print()
    print("PHASE 2: Fine-tuning ResNet layer4 + classifier")

    for param in model.layer4.parameters():
        param.requires_grad = True

    for param in model.fc.parameters():
        param.requires_grad = True

    optimizer = torch.optim.AdamW(
        filter(
            lambda p: p.requires_grad,
            model.parameters()
        ),
        lr=FINETUNE_LR,
        weight_decay=WEIGHT_DECAY
    )

    best_f1 = -1
    best_state = None

    patience_counter = 0

    for epoch in range(FINETUNE_EPOCHS):

        model.train()

        running_loss = 0.0

        for images, labels in train_loader:

            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

        val_accuracy, val_f1 = validate(
            model,
            val_loader
        )

        print(
            f"Fine Epoch {epoch + 1}/{FINETUNE_EPOCHS} | "
            f"Loss: {running_loss / len(train_loader):.4f} | "
            f"Val Accuracy: {val_accuracy:.4f} | "
            f"Val F1: {val_f1:.4f}"
        )

        if val_f1 > best_f1:

            best_f1 = val_f1

            best_state = copy.deepcopy(
                model.state_dict()
            )

            patience_counter = 0

        else:

            patience_counter += 1

        if patience_counter >= PATIENCE:

            print("Early stopping.")

            break

    # --------------------------------------------------------
    # LOAD BEST MODEL
    # --------------------------------------------------------

    if best_state is not None:

        model.load_state_dict(
            best_state
        )

    final_accuracy, final_f1 = validate(
        model,
        val_loader
    )

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    model_path = os.path.join(
        MODEL_DIR,
        f"{category}_classifier_improved.pth"
    )

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "class_names": class_names,
            "image_size": IMAGE_SIZE
        },
        model_path
    )

    print()
    print("BEST VALIDATION RESULTS")
    print("Accuracy:", round(final_accuracy, 4))
    print("F1:", round(final_f1, 4))

    print()
    print("Model saved:")
    print(model_path)


# ============================================================
# MAIN
# ============================================================

for category in categories:

    train_category(category)


print()
print("=" * 70)
print("IMPROVED TRAINING COMPLETE")
print("=" * 70)
print("Categories trained:", len(categories))
print("=" * 70)