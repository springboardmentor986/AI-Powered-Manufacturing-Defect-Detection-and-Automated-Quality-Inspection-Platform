"""Bottle-only supervised defect classifier for the MVTec samples."""

import json
import pickle
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from skimage.feature import hog
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

LABELS = ["good", "contamination", "broken_small", "broken_large"]
PRODUCT_CATEGORY = "bottle"
MODEL_VERSION = 4
MODEL_PATH = Path(__file__).resolve().parent / "defect_model.pkl"
METADATA_PATH = Path(__file__).resolve().parent / "defect_model.json"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}


def is_compatible_model(model):
    if not isinstance(model, dict):
        return False
    if model.get("version") != MODEL_VERSION:
        return False
    if model.get("labels") != LABELS:
        return False
    if not isinstance(model.get("binary_classifiers"), dict):
        return False
    if not isinstance(model.get("subtype_classifiers"), dict):
        return False
    if not model.get("feature_count"):
        return False
    return True


def normalize_label(folder):
    if folder == "good":
        return "good"
    if folder in {"contamination", "metal_contamination", "glue", "thread"}:
        return "contamination"
    if folder in {"broken_large", "broken"}:
        return "broken_large"
    return "broken_small"


def extract_features(image):
    resized = cv2.resize(image, (64, 64), interpolation=cv2.INTER_AREA)
    gray = cv2.equalizeHist(cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY))
    edges = cv2.Canny(gray, 50, 150)
    texture = hog(gray, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2), feature_vector=True)
    histogram = cv2.calcHist([resized], [0, 1], None, [8, 8], [0, 256, 0, 256]).flatten()
    histogram = histogram / max(float(histogram.sum()), 1.0)
    return np.concatenate([
        (gray.astype(np.float32) / 255).flatten(),
        (edges.astype(np.float32) / 255).flatten(),
        texture.astype(np.float32),
        histogram.astype(np.float32),
    ])


def load_samples(dataset_root=None):
    root = Path(dataset_root or Path(__file__).resolve().parent / "data" / "mvtec_ad")
    samples = []
    category_dir = root / PRODUCT_CATEGORY
    test_dir = category_dir / "test"
    if not test_dir.exists():
        return samples
    for defect_dir in sorted(test_dir.iterdir()):
        if not defect_dir.is_dir():
            continue
        label = normalize_label(defect_dir.name)
        for image_path in sorted(defect_dir.iterdir()):
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if image is not None:
                samples.append({"label": label, "category": PRODUCT_CATEGORY, "path": str(image_path), "features": extract_features(image)})
    return samples


def build_model(samples):
    grouped = defaultdict(list)
    for sample in samples:
        if sample["category"] == PRODUCT_CATEGORY:
            grouped[PRODUCT_CATEGORY].append(sample)
    binary_classifiers = {}
    subtype_classifiers = {}
    for category, category_samples in grouped.items():
        features = np.asarray([sample["features"] for sample in category_samples], dtype=np.float32)
        labels = [sample["label"] for sample in category_samples]
        binary_classifiers[category] = make_pipeline(
            StandardScaler(),
            RandomForestClassifier(n_estimators=300, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=-1),
        ).fit(features, [label != "good" for label in labels])
        defect_samples = [(feature, label) for feature, label in zip(features, labels) if label != "good"]
        subtype_classifiers[category] = make_pipeline(
            StandardScaler(),
            RandomForestClassifier(n_estimators=300, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=-1),
        ).fit(np.asarray([item[0] for item in defect_samples]), [item[1] for item in defect_samples])
    return {
        "version": MODEL_VERSION,
        "feature_count": len(samples[0]["features"]) if samples else 0,
        "labels": LABELS,
        "sample_counts": dict(Counter(sample["label"] for sample in samples)),
        "binary_classifiers": binary_classifiers,
        "subtype_classifiers": subtype_classifiers,
    }


def train_model(dataset_root=None):
    model = build_model(load_samples(dataset_root))
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(model, model_file)
    METADATA_PATH.write_text(json.dumps({
        "version": model["version"],
        "feature_count": model["feature_count"],
        "labels": model["labels"],
        "sample_counts": model["sample_counts"],
        "training_samples": sum(model["sample_counts"].values()),
    }), encoding="utf-8")
    return model


def load_model():
    if not MODEL_PATH.exists():
        return train_model()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error", category=InconsistentVersionWarning)
            with MODEL_PATH.open("rb") as model_file:
                model = pickle.load(model_file)
        if not is_compatible_model(model):
            raise ValueError("Stored model is stale or incompatible")
        return model
    except Exception:
        if MODEL_PATH.exists():
            try:
                MODEL_PATH.unlink()
            except OSError:
                pass
        return train_model()


def predict(image, model=None, category=None):
    model = model or load_model()
    features = extract_features(image).reshape(1, -1)
    binary_classifiers = model["binary_classifiers"]
    subtype_classifiers = model["subtype_classifiers"]
    classifier = binary_classifiers.get(category) if category else None
    if classifier is None:
        classifier = next(iter(binary_classifiers.values()))
    binary_probabilities = classifier.predict_proba(features)[0]
    bad_index = list(classifier.classes_).index(True)
    bad_confidence = float(binary_probabilities[bad_index])
    if not bool(classifier.predict(features)[0]):
        return {"label": "good", "confidence": round(1 - bad_confidence, 4), "nearest_distance": 0, "neighbors": 1}
    subtype_classifier = subtype_classifiers.get(category) or next(iter(subtype_classifiers.values()))
    subtype_probabilities = subtype_classifier.predict_proba(features)[0]
    subtype_index = int(np.argmax(subtype_probabilities))
    return {"label": str(subtype_classifier.classes_[subtype_index]), "confidence": round(float(subtype_probabilities[subtype_index]) * bad_confidence, 4), "nearest_distance": 0, "neighbors": 1}
