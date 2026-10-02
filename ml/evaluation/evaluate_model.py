import os
import sys

# Add the ml directory to Python's import path
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import cv2
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from models.autoencoder import ConvAutoencoder


# --------------------------------------------------
# Configuration
# --------------------------------------------------

IMAGE_SIZE = (224, 224)

DATASET_DIR = r"D:\VisionInspectAI\ml\dataset\bottle"

TRAIN_GOOD_DIR = os.path.join(
    DATASET_DIR,
    "train",
    "good"
)

TEST_GOOD_DIR = os.path.join(
    DATASET_DIR,
    "test",
    "good"
)

TEST_DEFECT_DIRS = [
    os.path.join(DATASET_DIR, "test", "broken_large"),
    os.path.join(DATASET_DIR, "test", "broken_small"),
    os.path.join(DATASET_DIR, "test", "contamination")
]

MODEL_PATH = r"D:\VisionInspectAI\ml\saved_models\bottle_autoencoder_improved.pth"


# --------------------------------------------------
# Device
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)


# --------------------------------------------------
# Image preprocessing
# --------------------------------------------------

def load_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return None

    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = image.astype(
        np.float32
    ) / 255.0

    image = torch.tensor(
        image
    ).permute(2, 0, 1)

    return image


# --------------------------------------------------
# Load model
# --------------------------------------------------

print("\nLoading improved trained model...")

model = ConvAutoencoder().to(device)

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=device
    )
)

model.eval()

print("Improved model loaded successfully!")


# --------------------------------------------------
# Calculate reconstruction error
# --------------------------------------------------

def calculate_score(image_tensor):

    image_tensor = image_tensor.unsqueeze(0).to(device)

    with torch.no_grad():

        reconstructed = model(image_tensor)

        error = torch.mean(
            (image_tensor - reconstructed) ** 2
        )

    return error.item()


# --------------------------------------------------
# Calculate training-good scores
# --------------------------------------------------

print("\nCalculating normal training scores...")

training_scores = []

for filename in os.listdir(TRAIN_GOOD_DIR):

    if filename.lower().endswith(
        (".png", ".jpg", ".jpeg")
    ):

        path = os.path.join(
            TRAIN_GOOD_DIR,
            filename
        )

        image = load_image(path)

        if image is not None:

            score = calculate_score(image)

            training_scores.append(score)


training_scores = np.array(
    training_scores
)


# --------------------------------------------------
# Determine anomaly threshold
# --------------------------------------------------

threshold = np.percentile(
    training_scores,
    95
)

print(
    f"Anomaly threshold: {threshold:.6f}"
)


# --------------------------------------------------
# Evaluate test images
# --------------------------------------------------

y_true = []
y_pred = []
scores = []

print("\nEvaluating test images...")


# Good images

good_count = 0

for filename in os.listdir(TEST_GOOD_DIR):

    if filename.lower().endswith(
        (".png", ".jpg", ".jpeg")
    ):

        path = os.path.join(
            TEST_GOOD_DIR,
            filename
        )

        image = load_image(path)

        if image is not None:

            score = calculate_score(image)

            prediction = 1 if score > threshold else 0

            y_true.append(0)
            y_pred.append(prediction)
            scores.append(score)

            good_count += 1


# Defect images

defect_count = 0

for defect_dir in TEST_DEFECT_DIRS:

    if not os.path.exists(defect_dir):
        continue

    for filename in os.listdir(defect_dir):

        if filename.lower().endswith(
            (".png", ".jpg", ".jpeg")
        ):

            path = os.path.join(
                defect_dir,
                filename
            )

            image = load_image(path)

            if image is not None:

                score = calculate_score(image)

                prediction = 1 if score > threshold else 0

                y_true.append(1)
                y_pred.append(prediction)
                scores.append(score)

                defect_count += 1


# --------------------------------------------------
# Metrics
# --------------------------------------------------

accuracy = accuracy_score(
    y_true,
    y_pred
)

precision = precision_score(
    y_true,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_true,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0
)

matrix = confusion_matrix(
    y_true,
    y_pred
)


# --------------------------------------------------
# Results
# --------------------------------------------------

print("\n" + "=" * 50)

print("IMPROVED MODEL EVALUATION RESULTS")

print("=" * 50)

print(
    f"Good test images   : {good_count}"
)

print(
    f"Defect test images : {defect_count}"
)

print(
    f"Threshold          : {threshold:.6f}"
)

print(
    f"Accuracy           : {accuracy:.4f}"
)

print(
    f"Precision          : {precision:.4f}"
)

print(
    f"Recall             : {recall:.4f}"
)

print(
    f"F1 Score           : {f1:.4f}"
)

print("\nConfusion Matrix:")

print(matrix)

print("\n" + "=" * 50)

print("EVALUATION COMPLETED!")

print("=" * 50)