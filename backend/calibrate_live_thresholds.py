
import os
import random
import json
import torch
import numpy as np

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features

DATASET_PATH = r"C:\Users\chand\Downloads\mvtec_anomaly_detection"
FEATURES_PATH = "normal_features.pt"
OUTPUT_PATH = "live_thresholds_calibrated.json"

SPLIT_SEED = 42
NORMAL_QUANTILE = 0.80

normal_features = torch.load(
    FEATURES_PATH, map_location="cpu", weights_only=False
)

def image_files(folder):
    if not os.path.isdir(folder):
        return []
    return sorted(
        name for name in os.listdir(folder)
        if name.lower().endswith((".png", ".jpg", ".jpeg"))
    )

def extract_image_features(path):
    with open(path, "rb") as f:
        image_bytes = f.read()
    image = preprocess_image(image_bytes)
    return extract_features(image).detach().cpu().reshape(-1)

thresholds = {}

for category, reference_features in normal_features.items():
    print(f"\nCalibrating {category}...")

    good_path = os.path.join(
        DATASET_PATH, category, "train", "good"
    )

    filenames = image_files(good_path)
    random.Random(f"{SPLIT_SEED}-{category}").shuffle(filenames)

    reference_count = int(len(filenames) * 0.80)
    validation_files = filenames[reference_count:]

    if not validation_files:
        raise RuntimeError(f"No validation images for {category}")

    normal_center = reference_features.mean(dim=0).reshape(-1)

    scores = []
    for filename in validation_files:
        path = os.path.join(good_path, filename)
        features = extract_image_features(path)
        scores.append(
            float(torch.norm(features - normal_center).item())
        )

    threshold = float(np.quantile(scores, NORMAL_QUANTILE))
    thresholds[category] = round(threshold, 6)
    print(
        f"Validation images: {len(scores)} | "
        f"Threshold: {threshold:.6f}"
    )

if len(thresholds) != 15:
    raise RuntimeError("Expected thresholds for all 15 categories")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(thresholds, f, indent=2)

print(f"\nSaved candidate thresholds to {OUTPUT_PATH}")
print("These are candidates; test-set evaluation is still required.")
