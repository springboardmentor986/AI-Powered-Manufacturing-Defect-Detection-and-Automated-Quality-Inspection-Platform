import os
import csv
import torch
import torch.nn as nn
from torchvision import models, transforms, datasets
from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


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

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "classification",
    "evaluation_results"
)

os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("CLASSIFIER EVALUATION")
print("=" * 70)
print("Device:", device)
print()


# ============================================================
# TEST TRANSFORM
# ============================================================

test_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# CATEGORIES
# ============================================================

categories = [
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
# CREATE MODEL
# ============================================================

def create_model(num_classes):

    model = models.resnet18(weights=None)

    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(
            model.fc.in_features,
            num_classes
        )
    )

    return model


# ============================================================
# EVALUATE ONE CATEGORY
# ============================================================

def evaluate_category(category):

    print("-" * 70)
    print("Category:", category)

    test_dir = os.path.join(
        DATASET_DIR,
        category,
        "test"
    )

    model_path = os.path.join(
        MODEL_DIR,
        f"{category}_classifier.pth"
    )

    if not os.path.exists(test_dir):
        print("Test dataset not found:", test_dir)
        return None

    if not os.path.exists(model_path):
        print("Model not found:", model_path)
        return None

    # --------------------------------------------------------
    # LOAD TEST DATA
    # --------------------------------------------------------

    test_dataset = datasets.ImageFolder(
        test_dir,
        transform=test_transform
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=16,
        shuffle=False,
        num_workers=0
    )

    class_names = test_dataset.classes

    print("Classes:", class_names)
    print("Test images:", len(test_dataset))

    # --------------------------------------------------------
    # LOAD MODEL CHECKPOINT
    # --------------------------------------------------------

    checkpoint = torch.load(
        model_path,
        map_location=device
    )

    # The training script saved class_names inside checkpoint.
    saved_class_names = checkpoint.get(
        "class_names",
        class_names
    )

    # --------------------------------------------------------
    # CREATE MODEL
    # --------------------------------------------------------

    model = create_model(
        len(saved_class_names)
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(device)
    model.eval()

    # --------------------------------------------------------
    # PREDICTIONS
    # --------------------------------------------------------

    all_predictions = []
    all_labels = []

    with torch.no_grad():

        for images, labels in test_loader:

            images = images.to(device)

            outputs = model(images)

            predictions = torch.argmax(
                outputs,
                dim=1
            )

            all_predictions.extend(
                predictions.cpu().numpy()
            )

            all_labels.extend(
                labels.numpy()
            )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    accuracy = accuracy_score(
        all_labels,
        all_predictions
    )

    precision = precision_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    recall = recall_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    f1 = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    cm = confusion_matrix(
        all_labels,
        all_predictions,
        labels=list(range(len(class_names)))
    )

    print()
    print("Accuracy :", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall   :", round(recall, 4))
    print("F1-score :", round(f1, 4))

    # --------------------------------------------------------
    # SAVE CONFUSION MATRIX
    # --------------------------------------------------------

    confusion_file = os.path.join(
        RESULTS_DIR,
        f"{category}_confusion_matrix.csv"
    )

    with open(
        confusion_file,
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            ["Actual \\ Predicted"] + class_names
        )

        for i, row in enumerate(cm):

            writer.writerow(
                [class_names[i]] + row.tolist()
            )

    print(
        "Confusion matrix saved:",
        confusion_file
    )

    return {
        "category": category,
        "test_images": len(test_dataset),
        "classes": len(class_names),
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1
    }


# ============================================================
# MAIN
# ============================================================

results = []

for category in categories:

    result = evaluate_category(category)

    if result is not None:
        results.append(result)

    print()


# ============================================================
# SAVE SUMMARY
# ============================================================

summary_file = os.path.join(
    BASE_DIR,
    "classification",
    "classification_evaluation_results.csv"
)

with open(
    summary_file,
    "w",
    newline=""
) as f:

    fieldnames = [
        "category",
        "test_images",
        "classes",
        "accuracy",
        "precision_macro",
        "recall_macro",
        "f1_macro"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for result in results:
        writer.writerow(result)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)

print("Categories evaluated:", len(results))
print()
print("Results saved to:")
print(summary_file)

print()
print("Confusion matrices saved to:")
print(RESULTS_DIR)

print("=" * 70)