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
    f1_score
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

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "classification",
    "original_vs_improved.csv"
)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 75)
print("ORIGINAL VS IMPROVED CLASSIFIER COMPARISON")
print("=" * 75)
print("Device:", device)
print()


# ============================================================
# CATEGORIES
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
# CREATE MODEL
# IMPORTANT:
# This matches the architecture used during training.
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
# EVALUATE ONE MODEL
# ============================================================

def evaluate_model(
    model_path,
    test_loader,
    class_names
):

    checkpoint = torch.load(
        model_path,
        map_location=device
    )

    saved_classes = checkpoint.get(
        "class_names",
        class_names
    )

    model = create_model(
        len(saved_classes)
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(device)

    model.eval()

    all_labels = []
    all_predictions = []

    with torch.no_grad():

        for images, labels in test_loader:

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

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


# ============================================================
# MAIN COMPARISON
# ============================================================

results = []


for category in categories:

    print()
    print("=" * 75)
    print("CATEGORY:", category)
    print("=" * 75)

    # --------------------------------------------------------
    # TEST DATA
    # --------------------------------------------------------

    test_dir = os.path.join(
        DATASET_DIR,
        category,
        "test"
    )

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

    print(
        "Test images:",
        len(test_dataset)
    )

    # --------------------------------------------------------
    # ORIGINAL MODEL
    # --------------------------------------------------------

    original_model = os.path.join(
        MODEL_DIR,
        f"{category}_classifier.pth"
    )

    # --------------------------------------------------------
    # IMPROVED MODEL
    # --------------------------------------------------------

    improved_model = os.path.join(
        MODEL_DIR,
        f"{category}_classifier_improved.pth"
    )

    # --------------------------------------------------------
    # CHECK FILES
    # --------------------------------------------------------

    if not os.path.exists(original_model):

        print(
            "Original model missing:",
            original_model
        )

        continue

    if not os.path.exists(improved_model):

        print(
            "Improved model missing:",
            improved_model
        )

        continue

    # --------------------------------------------------------
    # EVALUATE ORIGINAL
    # --------------------------------------------------------

    print()
    print("Evaluating ORIGINAL model...")

    original = evaluate_model(
        original_model,
        test_loader,
        class_names
    )

    # --------------------------------------------------------
    # EVALUATE IMPROVED
    # --------------------------------------------------------

    print("Evaluating IMPROVED model...")

    improved = evaluate_model(
        improved_model,
        test_loader,
        class_names
    )

    # --------------------------------------------------------
    # IMPROVEMENT
    # --------------------------------------------------------

    accuracy_change = (
        improved["accuracy"]
        - original["accuracy"]
    )

    precision_change = (
        improved["precision"]
        - original["precision"]
    )

    recall_change = (
        improved["recall"]
        - original["recall"]
    )

    f1_change = (
        improved["f1"]
        - original["f1"]
    )

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    if improved["f1"] > original["f1"]:

        decision = "IMPROVED_MODEL_BETTER"

    elif improved["f1"] < original["f1"]:

        decision = "ORIGINAL_MODEL_BETTER"

    else:

        decision = "SAME"

    # --------------------------------------------------------
    # PRINT RESULTS
    # --------------------------------------------------------

    print()
    print("ORIGINAL")
    print(
        f"Accuracy : {original['accuracy'] * 100:.2f}%"
    )
    print(
        f"Precision: {original['precision'] * 100:.2f}%"
    )
    print(
        f"Recall   : {original['recall'] * 100:.2f}%"
    )
    print(
        f"F1       : {original['f1'] * 100:.2f}%"
    )

    print()
    print("IMPROVED")
    print(
        f"Accuracy : {improved['accuracy'] * 100:.2f}%"
    )
    print(
        f"Precision: {improved['precision'] * 100:.2f}%"
    )
    print(
        f"Recall   : {improved['recall'] * 100:.2f}%"
    )
    print(
        f"F1       : {improved['f1'] * 100:.2f}%"
    )

    print()
    print("CHANGE")
    print(
        f"Accuracy : {accuracy_change * 100:+.2f}%"
    )
    print(
        f"Precision: {precision_change * 100:+.2f}%"
    )
    print(
        f"Recall   : {recall_change * 100:+.2f}%"
    )
    print(
        f"F1       : {f1_change * 100:+.2f}%"
    )

    print()
    print("DECISION:", decision)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    results.append({
        "category": category,

        "original_accuracy":
            round(original["accuracy"], 4),

        "improved_accuracy":
            round(improved["accuracy"], 4),

        "accuracy_change":
            round(accuracy_change, 4),

        "original_precision":
            round(original["precision"], 4),

        "improved_precision":
            round(improved["precision"], 4),

        "precision_change":
            round(precision_change, 4),

        "original_recall":
            round(original["recall"], 4),

        "improved_recall":
            round(improved["recall"], 4),

        "recall_change":
            round(recall_change, 4),

        "original_f1":
            round(original["f1"], 4),

        "improved_f1":
            round(improved["f1"], 4),

        "f1_change":
            round(f1_change, 4),

        "decision":
            decision
    })


# ============================================================
# SAVE COMPARISON CSV
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    newline=""
) as file:

    fieldnames = [
        "category",

        "original_accuracy",
        "improved_accuracy",
        "accuracy_change",

        "original_precision",
        "improved_precision",
        "precision_change",

        "original_recall",
        "improved_recall",
        "recall_change",

        "original_f1",
        "improved_f1",
        "f1_change",

        "decision"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(results)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print()
print("=" * 75)
print("FINAL COMPARISON")
print("=" * 75)

print()

for result in results:

    print(
        f"{result['category']:12s} | "
        f"F1: "
        f"{result['original_f1'] * 100:6.2f}% -> "
        f"{result['improved_f1'] * 100:6.2f}% | "
        f"{result['decision']}"
    )


print()
print("=" * 75)
print("COMPARISON COMPLETE")
print("=" * 75)

print()
print("Results saved to:")
print(OUTPUT_FILE)

print("=" * 75)