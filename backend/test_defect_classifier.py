import os
import joblib
import numpy as np

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features


# ============================================================
# PATHS
# ============================================================

DATASET_PATH = "dataset/mvtec_anomaly_detection"

CLASSIFIER_PATH = "backend/defect_classifier.pkl"


# ============================================================
# SETTINGS
# ============================================================

CATEGORY = "bottle"

DEFECT_CLASSES = [
    "broken_large",
    "broken_small",
    "contamination"
]


# ============================================================
# LOAD CLASSIFIER
# ============================================================

classifier = joblib.load(CLASSIFIER_PATH)

print("\n========================================")
print("VisionInspect AI")
print("Defect Classifier Test")
print("========================================")

print(f"\nCategory: {CATEGORY}")


# ============================================================
# TEST EACH DEFECT CLASS
# ============================================================

total = 0
correct = 0


for defect_class in DEFECT_CLASSES:

    folder_path = os.path.join(
        DATASET_PATH,
        CATEGORY,
        "test",
        defect_class
    )

    print("\n----------------------------------------")
    print(f"Testing: {defect_class}")
    print("----------------------------------------")


    image_files = [
        file
        for file in os.listdir(folder_path)
        if file.lower().endswith(
            (".png", ".jpg", ".jpeg")
        )
    ]


    for image_file in image_files:

        image_path = os.path.join(
            folder_path,
            image_file
        )

        try:

            with open(image_path, "rb") as file:
                image_bytes = file.read()


            # ----------------------------------------
            # Preprocess
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
                .reshape(1, -1)
            )


            # ----------------------------------------
            # Predict defect type
            # ----------------------------------------

            prediction = classifier.predict(
                feature_vector
            )[0]


            total += 1


            if prediction == defect_class:
                correct += 1


            print(
                f"{image_file} | "
                f"Actual: {defect_class} | "
                f"Predicted: {prediction}"
            )


        except Exception as error:

            print(
                f"Error processing {image_file}: "
                f"{error}"
            )


# ============================================================
# ACCURACY
# ============================================================

if total > 0:

    accuracy = (
        correct / total
    ) * 100

else:

    accuracy = 0


print("\n========================================")
print("DEFECT CLASSIFICATION RESULT")
print("========================================")

print(
    f"Correct predictions: {correct}/{total}"
)

print(
    f"Classification Accuracy: {accuracy:.2f}%"
)

print("========================================")