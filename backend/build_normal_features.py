
import os
import random
import torch

from backend.preprocess import preprocess_image
from backend.feature_extractor import extract_features

DATASET_PATH = r"C:\Users\chand\Downloads\mvtec_anomaly_detection"
OUTPUT_PATH = "normal_features.pt"
SPLIT_SEED = 42
REFERENCE_RATIO = 0.80

CATEGORIES = [
    "bottle", "cable", "capsule", "carpet", "grid",
    "hazelnut", "leather", "metal_nut", "pill", "screw",
    "tile", "toothbrush", "transistor", "wood", "zipper"
]

all_normal_features = {}

for category in CATEGORIES:
    print(f"\nProcessing category: {category}")

    good_path = os.path.join(
        DATASET_PATH, category, "train", "good"
    )

    if not os.path.isdir(good_path):
        print(f"WARNING: Path not found: {good_path}")
        continue

    filenames = sorted(
        name for name in os.listdir(good_path)
        if name.lower().endswith((".png", ".jpg", ".jpeg"))
    )

    random.Random(f"{SPLIT_SEED}-{category}").shuffle(filenames)

    reference_count = int(len(filenames) * REFERENCE_RATIO)
    reference_files = filenames[:reference_count]

    features = []

    for filename in reference_files:
        image_path = os.path.join(good_path, filename)

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        image = preprocess_image(image_bytes)
        feature = extract_features(image)
        features.append(feature)

    if features:
        all_normal_features[category] = torch.cat(features, dim=0)
        print(
            f"{category}: {len(features)} reference images, "
            f"{all_normal_features[category].shape}"
        )

if len(all_normal_features) != len(CATEGORIES):
    raise RuntimeError(
        "Not all 15 categories were processed. "
        "Original database has not been saved by this run."
    )

torch.save(all_normal_features, OUTPUT_PATH)

print("\nReference database saved:", OUTPUT_PATH)
print("Categories:", len(all_normal_features))