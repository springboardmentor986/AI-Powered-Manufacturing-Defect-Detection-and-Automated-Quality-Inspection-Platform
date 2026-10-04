"""Audit an extracted MVTec AD tree before model training."""

import json
from collections import Counter
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}


def audit(root=None):
    dataset_root = Path(root or Path(__file__).resolve().parent / "data" / "mvtec_ad")
    report = {"root": str(dataset_root), "categories": {}, "total_images": 0}
    if not dataset_root.exists():
        report["error"] = "Dataset root does not exist"
        return report
    for category in sorted(path for path in dataset_root.iterdir() if path.is_dir()):
        counts = Counter()
        ground_truth_masks = 0
        for image_path in category.rglob("*"):
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                relative_parts = image_path.relative_to(category).parts
                split = relative_parts[0] if relative_parts else "unknown"
                counts[split] += 1
                report["total_images"] += 1
        ground_truth = category / "ground_truth"
        if ground_truth.exists():
            ground_truth_masks = sum(1 for path in ground_truth.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
        report["categories"][category.name] = {"images": dict(counts), "ground_truth_masks": ground_truth_masks}
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
