import os

DATASET_PATH = "dataset/mvtec_ad"

print("=" * 50)
print("VisionInspect AI - Dataset Verification")
print("=" * 50)

if not os.path.exists(DATASET_PATH):
    print("Dataset folder not found.")
    exit()

print(f"Dataset path: {DATASET_PATH}")

categories = os.listdir(DATASET_PATH)

print(f"Categories found: {len(categories)}")

for category in categories:
    category_path = os.path.join(DATASET_PATH, category)

    if os.path.isdir(category_path):
        print(f"  ✓ {category}")

print("=" * 50)
print("Dataset directory verification completed.")
print("=" * 50)