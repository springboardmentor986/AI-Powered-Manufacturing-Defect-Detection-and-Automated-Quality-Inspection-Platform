from pathlib import Path
import json
import copy

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "classification" / "dataset"

MODEL_DIR = BASE_DIR / "classification" / "saved_models"

RESULTS_FILE = (
    BASE_DIR /
    "classification" /
    "training_results.json"
)


# ============================================================
# SETTINGS
# ============================================================

IMAGE_SIZE = 224

BATCH_SIZE = 16

EPOCHS = 20

LEARNING_RATE = 0.0005

RANDOM_SEED = 42

NUM_WORKERS = 0


CATEGORIES = [
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper"
]


# ============================================================
# DEVICE
# ============================================================

torch.manual_seed(RANDOM_SEED)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# IMAGE TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.RandomHorizontalFlip(
        p=0.5
    ),

    transforms.RandomRotation(
        10
    ),

    transforms.ColorJitter(
        brightness=0.15,
        contrast=0.15
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


eval_transform = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# CREATE MODEL
# ============================================================

def create_model(num_classes):

    weights = (
        models.ResNet18_Weights.DEFAULT
    )

    model = models.resnet18(
        weights=weights
    )

    # Freeze most of the pretrained network
    for parameter in model.parameters():
        parameter.requires_grad = False

    # Train the final classification layer
    input_features = model.fc.in_features

    model.fc = nn.Sequential(

        nn.Dropout(
            p=0.3
        ),

        nn.Linear(
            input_features,
            num_classes
        )
    )

    return model


# ============================================================
# LOAD DATASET
# ============================================================

def load_datasets(category):

    category_dir = (
        DATASET_DIR / category
    )

    train_dir = (
        category_dir / "train"
    )

    val_dir = (
        category_dir / "val"
    )

    train_dataset = datasets.ImageFolder(
        train_dir,
        transform=train_transform
    )

    val_dataset = datasets.ImageFolder(
        val_dir,
        transform=eval_transform
    )

    return (
        train_dataset,
        val_dataset
    )


# ============================================================
# TRAIN ONE CATEGORY
# ============================================================

def train_category(category):

    print()
    print("=" * 70)
    print(
        f"TRAINING CLASSIFIER: "
        f"{category.upper()}"
    )
    print("=" * 70)

    train_dataset, val_dataset = (
        load_datasets(category)
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS
    )

    class_names = train_dataset.classes

    num_classes = len(class_names)

    print()
    print(
        f"Training images   : "
        f"{len(train_dataset)}"
    )

    print(
        f"Validation images : "
        f"{len(val_dataset)}"
    )

    print(
        f"Classes           : "
        f"{num_classes}"
    )

    print()
    print("Class names:")

    for index, class_name in enumerate(
        class_names
    ):

        print(
            f"  {index}: {class_name}"
        )

    # --------------------------------------------------------
    # CREATE MODEL
    # --------------------------------------------------------

    model = create_model(
        num_classes
    )

    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(
        model.fc.parameters(),
        lr=LEARNING_RATE,
        weight_decay=0.0005
    )

    best_accuracy = 0.0

    best_model_weights = copy.deepcopy(
        model.state_dict()
    )

    # --------------------------------------------------------
    # TRAINING
    # --------------------------------------------------------

    for epoch in range(
        EPOCHS
    ):

        model.train()

        running_loss = 0.0

        correct = 0

        total = 0

        for images, labels in train_loader:

            images = images.to(
                DEVICE
            )

            labels = labels.to(
                DEVICE
            )

            optimizer.zero_grad()

            outputs = model(
                images
            )

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()

            optimizer.step()

            running_loss += (
                loss.item()
                * images.size(0)
            )

            _, predicted = torch.max(
                outputs,
                1
            )

            total += labels.size(0)

            correct += (
                predicted == labels
            ).sum().item()

        train_loss = (
            running_loss / total
            if total > 0
            else 0
        )

        train_accuracy = (
            correct / total
            if total > 0
            else 0
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        model.eval()

        val_correct = 0

        val_total = 0

        val_loss_total = 0.0

        with torch.no_grad():

            for images, labels in val_loader:

                images = images.to(
                    DEVICE
                )

                labels = labels.to(
                    DEVICE
                )

                outputs = model(
                    images
                )

                loss = criterion(
                    outputs,
                    labels
                )

                val_loss_total += (
                    loss.item()
                    * images.size(0)
                )

                _, predicted = torch.max(
                    outputs,
                    1
                )

                val_total += labels.size(0)

                val_correct += (
                    predicted == labels
                ).sum().item()

        val_loss = (
            val_loss_total / val_total
            if val_total > 0
            else 0
        )

        val_accuracy = (
            val_correct / val_total
            if val_total > 0
            else 0
        )

        print(
            f"Epoch "
            f"{epoch + 1:02d}/{EPOCHS} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Train Acc: {train_accuracy:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_accuracy:.4f}"
        )

        # ----------------------------------------------------
        # SAVE BEST MODEL
        # ----------------------------------------------------

        if val_accuracy > best_accuracy:

            best_accuracy = val_accuracy

            best_model_weights = copy.deepcopy(
                model.state_dict()
            )

    # --------------------------------------------------------
    # RESTORE BEST MODEL
    # --------------------------------------------------------

    model.load_state_dict(
        best_model_weights
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model_path = (
        MODEL_DIR /
        f"{category}_classifier.pth"
    )

    torch.save(
        {
            "model_state_dict":
                model.state_dict(),

            "class_names":
                class_names,

            "image_size":
                IMAGE_SIZE
        },
        model_path
    )

    print()
    print(
        f"Best validation accuracy: "
        f"{best_accuracy:.4f}"
    )

    print(
        f"Model saved to:"
    )

    print(model_path)

    return {
        "category": category,
        "classes": class_names,
        "num_classes": num_classes,
        "best_validation_accuracy":
            round(best_accuracy, 4),
        "model_path":
            str(model_path)
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("DEFECT CLASSIFIER TRAINING")
    print("=" * 70)

    print()
    print(f"Device      : {DEVICE}")
    print(f"Image size  : {IMAGE_SIZE}")
    print(f"Batch size  : {BATCH_SIZE}")
    print(f"Epochs      : {EPOCHS}")
    print(f"Learning rate: {LEARNING_RATE}")

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    for index, category in enumerate(
        CATEGORIES,
        start=1
    ):

        print()
        print(
            f"Overall progress: "
            f"{index}/{len(CATEGORIES)}"
        )

        try:

            result = train_category(
                category
            )

            results.append(result)

        except Exception as error:

            print()
            print(
                f"ERROR training "
                f"{category}:"
            )

            print(error)

    # --------------------------------------------------------
    # SAVE TRAINING RESULTS
    # --------------------------------------------------------

    with open(
        RESULTS_FILE,
        "w"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CLASSIFIER TRAINING COMPLETED")
    print("=" * 70)

    print()
    print(
        f"Successfully trained: "
        f"{len(results)}/{len(CATEGORIES)}"
    )

    for result in results:

        print(
            f"{result['category']:<15} "
            f"classes={result['num_classes']:<2} "
            f"val_acc="
            f"{result['best_validation_accuracy']:.4f}"
        )

    print()
    print(
        f"Models saved in:"
    )

    print(MODEL_DIR)

    print()
    print(
        f"Training results:"
    )

    print(RESULTS_FILE)

    print()
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()