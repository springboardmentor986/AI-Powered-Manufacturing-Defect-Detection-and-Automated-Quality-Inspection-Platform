import os
import joblib
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features


# ============================================================
# PATHS
# ============================================================

DATASET_PATH = "dataset/mvtec_anomaly_detection"

CATEGORY = "bottle"


# ============================================================
# DEFECT CLASSES
# ============================================================

DEFECT_CLASSES = [
    "broken_large",
    "broken_small",
    "contamination"
]


# ============================================================
# EXTRACT FEATURES
# ============================================================

features = []
labels = []

print("\n========================================")
print("VisionInspect AI")
print("Proper Defect Classification Evaluation")
print("========================================")

print(f"\nCategory: {CATEGORY}")


for defect_class in DEFECT_CLASSES:

    folder_path = os.path.join(
        DATASET_PATH,
        CATEGORY,
        "test",
        defect_class
    )

    image_files = [
        file
        for file in os.listdir(folder_path)
        if file.lower().endswith(
            (".png", ".jpg", ".jpeg")
        )
    ]

    print(
        f"\n{defect_class}: "
        f"{len(image_files)} images"
    )


    for image_file in image_files:

        image_path = os.path.join(
            folder_path,
            image_file
        )

        try:

            with open(image_path, "rb") as file:
                image_bytes = file.read()


            # Preprocess
            processed_image = preprocess_image(
                image_bytes
            )


            # ResNet18 feature extraction
            feature_tensor = extract_features(
                processed_image
            )


            feature_vector = (
                feature_tensor
                .squeeze()
                .numpy()
            )


            features.append(feature_vector)
            labels.append(defect_class)


        except Exception as error:

            print(
                f"Error processing "
                f"{image_file}: {error}"
            )


X = np.array(features)
y = np.array(labels)


print("\n========================================")
print("Feature Extraction Completed")
print("========================================")

print(
    f"Total samples: {len(X)}"
)

print(
    f"Feature shape: {X.shape}"
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42,
    stratify=y
)


print("\n========================================")
print("Dataset Split")
print("========================================")

print(
    f"Training samples: {len(X_train)}"
)

print(
    f"Testing samples: {len(X_test)}"
)


# ============================================================
# TRAIN CLASSIFIER
# ============================================================

print("\nTraining classifier...")

classifier = LogisticRegression(
    max_iter=1000,
    random_state=42
)

classifier.fit(
    X_train,
    y_train
)


# ============================================================
# PREDICTIONS
# ============================================================

y_pred = classifier.predict(
    X_test
)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)


# ============================================================
# RESULTS
# ============================================================

print("\n========================================")
print("DEFECT CLASSIFICATION RESULTS")
print("========================================")

print(
    f"Accuracy  : {accuracy * 100:.2f}%"
)

print(
    f"Precision : {precision * 100:.2f}%"
)

print(
    f"Recall    : {recall * 100:.2f}%"
)

print(
    f"F1 Score  : {f1 * 100:.2f}%"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n========================================")
print("Classification Report")
print("========================================")

print(
    classification_report(
        y_test,
        y_pred,
        labels=DEFECT_CLASSES,
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n========================================")
print("Confusion Matrix")
print("========================================")

matrix = confusion_matrix(
    y_test,
    y_pred,
    labels=DEFECT_CLASSES
)

print(
    "Labels:"
)

print(
    DEFECT_CLASSES
)

print(matrix)


print("\n========================================")
print("Evaluation Completed")
print("========================================")