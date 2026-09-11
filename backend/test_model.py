from pathlib import Path
import joblib
import numpy as np
from PIL import Image
from skimage.feature import hog

DATASET_PATH = Path("dataset/mvtec_ad/bottle")
MODEL_PATH = Path("backend/anomaly_model.pkl")

IMAGE_SIZE = (128, 128)


def extract_features(image_path):
    image = Image.open(image_path).convert("L")
    image = image.resize(IMAGE_SIZE)

    image_array = np.asarray(image, dtype=np.float32) / 255.0

    features = hog(
        image_array,
        orientations=9,
        pixels_per_cell=(16, 16),
        cells_per_block=(2, 2),
        block_norm="L2-Hys"
    )

    return features


def test_category(model, category):
    folder = DATASET_PATH / "test" / category
    images = sorted(folder.glob("*.png"))

    correct = 0

    print(f"\n--- {category.upper()} ---")

    for image_path in images:
        features = extract_features(image_path).reshape(1, -1)

        prediction = model.predict(features)[0]
        score = model.decision_function(features)[0]

        if prediction == 1:
            result = "NORMAL"
        else:
            result = "DEFECTIVE"

        expected = "NORMAL" if category == "good" else "DEFECTIVE"

        if result == expected:
            correct += 1

        print(f"{image_path.name:15} -> {result:10} Score: {score:.4f}")

    accuracy = (correct / len(images)) * 100

    print(f"Correct: {correct}/{len(images)}")
    print(f"Category Accuracy: {accuracy:.2f}%")

    return correct, len(images)


if __name__ == "__main__":

    print("=" * 60)
    print("VisionInspect AI - Model Testing")
    print("=" * 60)

    model = joblib.load(MODEL_PATH)

    total_correct = 0
    total_images = 0

    categories = [
        "good",
        "broken_large",
        "broken_small",
        "contamination"
    ]

    for category in categories:
        correct, total = test_category(model, category)
        total_correct += correct
        total_images += total

    overall_accuracy = (total_correct / total_images) * 100

    print("\n" + "=" * 60)
    print("FINAL MODEL EVALUATION")
    print("=" * 60)
    print(f"Total Images Tested : {total_images}")
    print(f"Correct Predictions : {total_correct}")
    print(f"Overall Accuracy    : {overall_accuracy:.2f}%")
    print("=" * 60)