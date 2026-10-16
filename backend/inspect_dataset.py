from pathlib import Path

dataset_path = Path("dataset/mvtec_anomaly_detection")

print("MVTec AD - Ground Truth Analysis")
print("================================")

for category in sorted(dataset_path.iterdir()):

    if not category.is_dir():
        continue

    ground_truth_path = category / "ground_truth"

    if ground_truth_path.exists():
        masks = list(ground_truth_path.rglob("*.png"))

        print(f"{category.name}: {len(masks)} ground-truth masks")
    else:
        print(f"{category.name}: ground_truth folder not found")