import os
import torch
import joblib
import numpy as np

from PIL import Image
from sklearn.linear_model import LogisticRegression

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features


# ============================================================
# PATHS
# ============================================================

DATASET_PATH = "dataset/mvtec_anomaly_detection"

OUTPUT_PATH = "backend/defect_classifier.pkl"


# ============================================================
# CATEGORY
# ============================================================

CATEGORY = "bottle"

DEFECT_CLASSES = [
    "broken_large",
    "broken_small",
    "contamination"
]


# ============================================================
# FEATURE EXTRACTION
# ============================================================

features = []
labels = []


print("\n========================================")
print("VisionInspect AI")
print("Defect Classifier Training")
print("========================================")

print(f"\nCategory: {CATEGORY}")


for defect_class in DEFECT_CLASSES:

    folder_path = os.path.join(
        DATASET_PATH,
        CATEGORY,
        "test",
        defect_class
    )

    print(
        f"\nProcessing: {defect_class}"
    )

    image_files = [
        file
        for file in os.listdir(folder_path)
        if file.lower().endswith(
            (".png", ".jpg", ".jpeg")
        )
    ]

    print(
        f"Images found: {len(image_files)}"
    )


    for image_file in image_files:

        image_path = os.path.join(
            folder_path,
            image_file
        )

        try:

            with open(image_path, "rb") as file:

                image_bytes = file.read()


            # ----------------------------------------
            # Preprocess image
            # ----------------------------------------

            processed_image = preprocess_image(
                image_bytes
            )


            # ----------------------------------------
            # Extract ResNet18 features
            # ----------------------------------------

            feature_tensor = extract_features(
                processed_image
            )


            feature_vector = (
                feature_tensor
                .squeeze()
                .numpy()
            )


            features.append(
                feature_vector
            )

            labels.append(
                defect_class
            )


        except Exception as error:

            print(
                f"Error processing {image_file}: "
                f"{error}"
            )


# ============================================================
# CONVERT TO NUMPY
# ============================================================

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
# TRAIN CLASSIFIER
# ============================================================

print("\nTraining defect classifier...")


classifier = LogisticRegression(
    max_iter=1000,
    random_state=42
)


classifier.fit(
    X,
    y
)


# ============================================================
# SAVE CLASSIFIER
# ============================================================

joblib.dump(
    classifier,
    OUTPUT_PATH
)


print("\n========================================")
print("Training Completed Successfully")
print("========================================")

print(
    f"Classes: {classifier.classes_}"
)

print(
    f"Classifier saved to: {OUTPUT_PATH}"
)

print("\nVisionInspect AI defect classifier ready!")