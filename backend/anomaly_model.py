from pathlib import Path
import joblib
import numpy as np
from PIL import Image
from skimage.feature import hog
from sklearn.ensemble import IsolationForest

DATASET_PATH = Path("dataset/mvtec_ad/bottle")
TRAIN_PATH = DATASET_PATH / "train" / "good"

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


def load_training_features():
    features = []

    for image_path in sorted(TRAIN_PATH.glob("*.png")):
        features.append(extract_features(image_path))

    return np.array(features)


if __name__ == "__main__":
    print("=" * 55)
    print("VisionInspect AI - Anomaly Detection Model")
    print("=" * 55)

    print("\nLoading normal bottle images...")

    X_train = load_training_features()

    print(f"Training images : {len(X_train)}")
    print(f"Feature shape   : {X_train.shape}")

    print("\nTraining Isolation Forest...")

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42
    )

    model.fit(X_train)

    model_path = Path("backend/anomaly_model.pkl")
    joblib.dump(model, model_path)

    print("\nModel training completed successfully.")
    print(f"Model saved to : {model_path}")

    print("=" * 55)